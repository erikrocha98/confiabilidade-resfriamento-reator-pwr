"""Frente 4 - Extensao dinamica da simulacao de Monte Carlo (Standby e Reparo).

Implementa a modelagem temporal nao capturada pela arvore de falhas estatica:

1. **Decomposicao de modos do INL** (``dados/extracao_bruta.csv``, Table 1):
   separa para cada componente a probabilidade de falha sob demanda (modos
   ``Beta``, como ``MDP-FTS-CCW``) da taxa de falha em operacao (modos ``Gamma``,
   como ``MDP-FTR-CCW``, ``MDP-ELS`` e ``MDP-ELL``), preservando exatamente o
   mapeamento oficial de ``scripts/montar_parametros.py``.
2. **Bomba em espera (cold / warm standby)** para os pares ``(MDP_A, MDP_C)`` e
   ``(MDP_B, MDP_D)``, sem alterar ``modelo/arvore_falhas.yaml``.
3. **Simulacao a Eventos Discretos (DES) com reparo**:
   suporta tempos medios de reparo (MTTR) exponenciais e politica de 1 ou 2
   equipes de reparo, calculando:
   - nao-confiabilidade na missao ``F(T)`` (falhou em algum instante de [0, T]);
   - indisponibilidade pontual ``U(T)`` (em falha no instante exato T);
   - indisponibilidade media ``U_bar(T)`` (fracao media do tempo em falha).

**Regra do repositorio (sem dados inventados):** este modulo NAO contem valores
numericos fixos de MTTR. O parametro ``mttr_h`` e opcional (padrao ``None``,
sem reparo) ou carregado de CSV externo com colunas ``fonte`` e
``pagina_tabela`` obrigatorias.
"""

from __future__ import annotations

import argparse
import heapq
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Permite rodar o script diretamente (ex.: python monte_carlo/dinamico.py).
RAIZ_REPO = Path(__file__).resolve().parent.parent
if str(RAIZ_REPO) not in sys.path:
    sys.path.insert(0, str(RAIZ_REPO))

from ccws import arvore as mod_arvore  # noqa: E402
from ccws import dados as mod_dados  # noqa: E402
from monte_carlo import simulacao as mc  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
CAMINHO_EXTRACAO_PADRAO = RAIZ_REPO / "dados" / "extracao_bruta.csv"

# Mesmo comprimento por trem documentado em scripts/montar_parametros.py e dados/README.md
PES_POR_TREM_PIPE = 2004.0

# Mapeamento oficial de codigos INL (Table 1) por componente (identico a montar_parametros.py)
MODOS_POR_COMPONENTE: dict[str, tuple[str, ...]] = {
    "MOV": ("MOV-FTOC", "MOV-SOP-CCW", "MOV-ILS", "MOV-ILL", "MOV-ELS", "MOV-ELL"),
    "CKV": ("CKV-FTO", "CKV-FTC", "CKV-SOP", "CKV-ILS", "CKV-ILL", "CKV-ELS", "CKV-ELL"),
    "XVM": ("XVM-FTOC", "XVM-SOP", "XVM-ILS", "XVM-ILL", "XVM-ELS", "XVM-ELL"),
    "FCV": ("FCV-FTOC", "FCV-FC", "FCV-SOP"),
    "MDP": ("MDP-FTS-CCW", "MDP-FTR-CCW", "MDP-ELS", "MDP-ELL"),
    "HTX": ("HTX-PG-CCW", "HTX-ILS", "HTX-ILL", "HTX-ELS", "HTX-ELL"),
    "PIPE": ("PIPE-OTHER-ELS", "PIPE-OTHER-ELL"),
    "STF": ("STF-FTOP-D", "STF-FTOP-R"),
    "STL": ("STL-FTOP-D", "STL-FTOP-R"),
    "STP": ("STP-FTOP-D", "STP-FTOP-R"),
    "STT": ("STT-FTOP-D", "STT-FTOP-R"),
}

# Pares (bomba principal, bomba reserva em espera) por trem, conforme arvore_falhas.yaml
PARES_BOMBAS: tuple[tuple[str, str, str], ...] = (
    ("A", "MDP_A", "MDP_C"),
    ("B", "MDP_B", "MDP_D"),
)


@dataclass(frozen=True)
class ParametrosComponente:
    """Parametros decompostos de um componente (demanda + taxa horaria)."""

    componente: str
    prob_demanda: float
    taxa_falha_h: float
    codigos_demanda: tuple[str, ...] = ()
    codigos_taxa: tuple[str, ...] = ()

    def prob_missao_estatica(self, tempo_missao_h: float) -> float:
        """Probabilidade de falha em serie: 1 - (1 - q_d) * exp(-lambda * T)."""
        return 1.0 - (1.0 - self.prob_demanda) * math.exp(
            -self.taxa_falha_h * tempo_missao_h
        )


# ------------------------------------------------------------------ carga INL
def carregar_parametros_decompostos(
    caminho_extracao: str | Path | None = None,
) -> dict[str, ParametrosComponente]:
    """Carrega ``prob_demanda`` e ``taxa_falha_h`` por componente da Table 1 do INL."""
    caminho = (
        Path(caminho_extracao)
        if caminho_extracao is not None
        else CAMINHO_EXTRACAO_PADRAO
    )
    if not caminho.is_file():
        raise mod_dados.ErroDados(f"arquivo de extracao nao encontrado: {caminho}")

    df = pd.read_csv(caminho)
    t1 = df[df["tabela"] == "Table 1"].set_index("modo_falha")

    resultado: dict[str, ParametrosComponente] = {}
    for comp, codigos in MODOS_POR_COMPONENTE.items():
        sobrevive_demanda = 1.0
        taxa_total = 0.0
        cod_dem: list[str] = []
        cod_tax: list[str] = []

        for codigo in codigos:
            if codigo not in t1.index:
                raise mod_dados.ErroDados(
                    f"modo de falha '{codigo}' ausente na Table 1 de {caminho.name}"
                )
            linha = t1.loc[codigo]
            if isinstance(linha, pd.DataFrame):
                linha = linha.iloc[0]

            media = float(linha["media"])
            dist = str(linha["distribuicao"]).strip()
            unidade = str(linha["unidade"]).strip()

            if dist == "Beta":
                sobrevive_demanda *= 1.0 - media
                cod_dem.append(codigo)
            elif dist == "Gamma":
                fator = PES_POR_TREM_PIPE if unidade == "por hora-pé" else 1.0
                taxa_total += media * fator
                cod_tax.append(codigo)
            else:
                raise mod_dados.ErroDados(
                    f"distribuicao inesperada '{dist}' para '{codigo}' em {caminho.name}"
                )

        resultado[comp] = ParametrosComponente(
            componente=comp,
            prob_demanda=1.0 - sobrevive_demanda,
            taxa_falha_h=taxa_total,
            codigos_demanda=tuple(cod_dem),
            codigos_taxa=tuple(cod_tax),
        )

    return resultado


def carregar_mttr_csv(caminho: str | Path) -> dict[str, float]:
    """Le tabela externa de MTTR (em horas), exigindo rastreabilidade de fonte.

    Colunas obrigatorias: ``componente``, ``mttr_h``, ``fonte``, ``pagina_tabela``.
    Celulas vazias em ``mttr_h`` sao ignoradas (componente tratado sem reparo).
    """
    arq = Path(caminho)
    if not arq.is_file():
        raise mod_dados.ErroDados(f"arquivo de MTTR nao encontrado: {arq}")

    df = pd.read_csv(arq, dtype=str, keep_default_na=True)
    obrigatorias = {"componente", "mttr_h", "fonte", "pagina_tabela"}
    faltantes = sorted(obrigatorias - set(df.columns))
    if faltantes:
        raise mod_dados.ErroDados(
            f"colunas obrigatorias ausentes em {arq.name}: {faltantes}"
        )

    mttr: dict[str, float] = {}
    for idx, linha in df.iterrows():
        val_txt = linha["mttr_h"]
        if pd.isna(val_txt) or not str(val_txt).strip():
            continue
        if pd.isna(linha["fonte"]) or not str(linha["fonte"]).strip():
            raise mod_dados.ErroDados(
                f"linha {int(idx) + 2} de {arq.name}: valor de mttr_h sem 'fonte'"
            )
        if pd.isna(linha["pagina_tabela"]) or not str(linha["pagina_tabela"]).strip():
            raise mod_dados.ErroDados(
                f"linha {int(idx) + 2} de {arq.name}: valor de mttr_h sem 'pagina_tabela'"
            )
        try:
            valor = float(str(val_txt).strip())
        except ValueError as exc:
            raise mod_dados.ErroDados(
                f"linha {int(idx) + 2} de {arq.name}: mttr_h nao numerico ({val_txt!r})"
            ) from exc
        if valor <= 0.0:
            raise mod_dados.ErroDados(
                f"linha {int(idx) + 2} de {arq.name}: mttr_h deve ser positivo ({valor})"
            )
        comp = str(linha["componente"]).strip()
        mttr[comp] = valor

    return mttr


# ------------------------------------------- solucoes analiticas de referencia
def prob_falha_standby_analitica(
    taxa_falha_h: float,
    prob_demanda_partida: float,
    tempo_missao_h: float,
    principal_parte_em_t0: bool = False,
) -> float:
    """Solucao analitica fechada de 1 principal + 1 reserva em espera fria (sem reparo).

    - Se ``principal_parte_em_t0=False`` (bomba principal ja operando em t=0):
      ``P = q_fts * (1 - exp(-lam*T)) + (1 - q_fts) * (1 - exp(-lam*T)*(1 + lam*T))``
    - Se ``principal_parte_em_t0=True`` (principal tambem sofre demanda em t=0):
      se falhar na partida (prob. ``q_fts``), a reserva e demandada em t=0 pelo
      tempo integral ``T``; caso contrario, aplica-se a expressao acima.
    """
    lam_t = taxa_falha_h * tempo_missao_h
    exp_lt = math.exp(-lam_t)
    q = prob_demanda_partida

    p_dado_principal_partiu = q * (1.0 - exp_lt) + (1.0 - q) * (
        1.0 - exp_lt * (1.0 + lam_t)
    )
    if not principal_parte_em_t0:
        return p_dado_principal_partiu

    p_reserva_em_t0 = 1.0 - (1.0 - q) * exp_lt
    return q * p_reserva_em_t0 + (1.0 - q) * p_dado_principal_partiu


# ----------------------------------------- motor DES para par de bombas (1+1)
def _des_uma_historia_par_bombas(
    t_falha_inicial: float,
    bomba_inicial_falha: int,
    tempo_missao_h: float,
    taxa_op: float,
    taxa_espera: float,
    prob_fts: float,
    mttr_h: float | None,
    n_equipes_reparo: int,
    gerador: np.random.Generator,
) -> tuple[bool, bool, float]:
    """Executa a simulacao a eventos discretos de 1 historia (1+1 bombas) a partir do 1o evento.

    Estados possiveis por bomba (indices 0 e 1):
      - ``"OP"``: operando (taxa ``taxa_op``);
      - ``"STBY"``: reserva em espera (taxa ``taxa_espera``, 0 em espera fria);
      - ``"REP"``: em reparo (tempo exponencial de media ``mttr_h``);
      - ``"FAIL"``: falhada aguardando equipe de reparo (ou sem reparo).

    Returns:
        ``(falhou_na_missao, em_falha_no_fim, tempo_em_falha)``
    """
    # Estado imediatamente ANTES do primeiro evento em t = t_falha_inicial:
    # bomba 0 estava OP, bomba 1 estava STBY.
    estados = ["OP", "STBY"]
    versao = [0, 0]  # invalida eventos antigos na fila de prioridade
    fila: list[tuple[float, int, str, int]] = []  # (tempo, bomba, tipo, versao)
    em_reparo = 0

    def agendar(tempo: float, bomba: int, tipo: str) -> None:
        if tempo < tempo_missao_h:
            versao[bomba] += 1
            heapq.heappush(fila, (tempo, bomba, tipo, versao[bomba]))

    def iniciar_reparo_se_possivel(t_atual: float, bomba: int) -> None:
        nonlocal em_reparo
        if mttr_h is None:
            estados[bomba] = "FAIL"
            return
        if em_reparo < n_equipes_reparo:
            estados[bomba] = "REP"
            em_reparo += 1
            agendar(t_atual + float(gerador.exponential(mttr_h)), bomba, "REPARO")
        else:
            estados[bomba] = "FAIL"

    def promover_espera(t_atual: float) -> None:
        """Se nenhuma bomba esta operando e existe uma em espera, tenta partir."""
        if "OP" in estados:
            return
        for b in (0, 1):
            if estados[b] == "STBY":
                # Invalida eventual falha em espera agendada
                versao[b] += 1
                if prob_fts > 0.0 and gerador.random() < prob_fts:
                    iniciar_reparo_se_possivel(t_atual, b)
                else:
                    estados[b] = "OP"
                    if taxa_op > 0.0:
                        agendar(
                            t_atual + float(gerador.exponential(1.0 / taxa_op)),
                            b,
                            "FALHA",
                        )
                return

    # Se a primeira falha foi na bomba 1 (espera morna), a bomba 0 ainda precisa
    # ter seu tempo de falha restante agendado (propriedade sem memoria da Exp).
    if bomba_inicial_falha == 1 and taxa_op > 0.0:
        agendar(
            t_falha_inicial + float(gerador.exponential(1.0 / taxa_op)), 0, "FALHA"
        )
    # Se a primeira falha foi na bomba 0 (operacao) e espera e morna, a bomba 1
    # continuava sã ate t_falha_inicial e sera promovida imediatamente abaixo.

    t_atual = t_falha_inicial
    # Processa a falha inicial em t_falha_inicial
    iniciar_reparo_se_possivel(t_atual, bomba_inicial_falha)
    promover_espera(t_atual)

    sistema_down = "OP" not in estados
    falhou_na_missao = sistema_down
    tempo_em_falha = 0.0

    while fila:
        t_ev, bomba, tipo, v_ev = heapq.heappop(fila)
        if v_ev != versao[bomba]:
            continue  # evento obsoleto

        if sistema_down:
            tempo_em_falha += t_ev - t_atual
        t_atual = t_ev

        if tipo == "FALHA":
            iniciar_reparo_se_possivel(t_atual, bomba)
            promover_espera(t_atual)
        elif tipo == "REPARO":
            em_reparo -= 1
            # Se outra bomba esta na fila aguardando equipe, inicia o reparo dela
            outra = 1 - bomba
            if estados[outra] == "FAIL" and mttr_h is not None and em_reparo < n_equipes_reparo:
                estados[outra] = "REP"
                em_reparo += 1
                agendar(t_atual + float(gerador.exponential(mttr_h)), outra, "REPARO")

            if "OP" not in estados:
                # Sistema estava fora: bomba recem-reparada assume operacao
                estados[bomba] = "OP"
                if taxa_op > 0.0:
                    agendar(
                        t_atual + float(gerador.exponential(1.0 / taxa_op)),
                        bomba,
                        "FALHA",
                    )
            else:
                # Outra bomba ja opera: bomba reparada vai para espera
                estados[bomba] = "STBY"
                if taxa_espera > 0.0:
                    agendar(
                        t_atual + float(gerador.exponential(1.0 / taxa_espera)),
                        bomba,
                        "FALHA",
                    )

        sistema_down = "OP" not in estados
        if sistema_down:
            falhou_na_missao = True

    if sistema_down:
        tempo_em_falha += tempo_missao_h - t_atual

    return falhou_na_missao, sistema_down, tempo_em_falha


def simular_par_bombas_standby(
    taxa_falha_h: float,
    prob_demanda_partida: float,
    tempo_missao_h: float,
    n_historias: int,
    gerador: np.random.Generator,
    mttr_h: float | None = None,
    fator_espera: float = 0.0,
    principal_parte_em_t0: bool = False,
    n_equipes_reparo: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simula um par de bombas (1 principal + 1 reserva em espera, com ou sem reparo).

    Usa filtro vetorizado de primeira falha em NumPy para evitar entrar no laco
    DES nas historias em que nenhum evento ocorre em ``[0, T]`` (matematicamente
    exato para tempos exponenciais sem memoria).

    Args:
        taxa_falha_h: taxa de falha em operacao ``lambda_op`` (1/h).
        prob_demanda_partida: probabilidade de falha ao partir ``q_fts``.
        tempo_missao_h: horizonte da missao ``T`` (h).
        n_historias: numero de historias.
        gerador: ``np.random.Generator``.
        mttr_h: tempo medio de reparo (h) ou ``None`` para sem reparo.
        fator_espera: razao ``lambda_espera / lambda_op`` (0.0 = cold standby).
        principal_parte_em_t0: se ``True``, a principal tambem sofre demanda em t=0.
        n_equipes_reparo: numero de equipes de reparo (1 ou 2).

    Returns:
        Tupla de arrays de tamanho ``n_historias``:
        ``(falhou_na_missao, em_falha_no_fim, fracao_tempo_falha)``.
    """
    if n_historias <= 0:
        raise ValueError("n_historias deve ser positivo")
    if tempo_missao_h <= 0.0:
        raise ValueError("tempo_missao_h deve ser positivo")
    if taxa_falha_h < 0.0:
        raise ValueError("taxa_falha_h deve ser nao negativa")
    if not (0.0 <= prob_demanda_partida <= 1.0):
        raise ValueError("prob_demanda_partida deve estar em [0, 1]")
    if not (0.0 <= fator_espera <= 1.0):
        raise ValueError("fator_espera deve estar em [0, 1]")
    if mttr_h is not None and mttr_h <= 0.0:
        raise ValueError("mttr_h deve ser positivo quando informado")
    if n_equipes_reparo not in (1, 2):
        raise ValueError("n_equipes_reparo deve ser 1 ou 2")

    taxa_espera = taxa_falha_h * fator_espera

    # ---- Caso rapido totalmente vetorizado: espera fria SEM reparo
    if mttr_h is None and taxa_espera == 0.0:
        t1 = (
            gerador.exponential(1.0 / taxa_falha_h, size=n_historias)
            if taxa_falha_h > 0.0
            else np.full(n_historias, np.inf)
        )
        if principal_parte_em_t0 and prob_demanda_partida > 0.0:
            falha_p0 = gerador.random(n_historias) < prob_demanda_partida
            t1 = np.where(falha_p0, 0.0, t1)

        falhou_principal = t1 < tempo_missao_h
        n_dem = int(np.count_nonzero(falhou_principal))

        falhou_par = np.zeros(n_historias, dtype=bool)
        fracao_falha = np.zeros(n_historias, dtype=float)

        if n_dem > 0:
            idx_dem = np.flatnonzero(falhou_principal)
            t1_dem = t1[idx_dem]

            falha_fts_res = (
                gerador.random(n_dem) < prob_demanda_partida
                if prob_demanda_partida > 0.0
                else np.zeros(n_dem, dtype=bool)
            )
            t2_dem = (
                gerador.exponential(1.0 / taxa_falha_h, size=n_dem)
                if taxa_falha_h > 0.0
                else np.full(n_dem, np.inf)
            )
            t_falha_par = np.where(falha_fts_res, t1_dem, t1_dem + t2_dem)
            par_caiu = t_falha_par < tempo_missao_h

            falhou_par[idx_dem] = par_caiu
            fracao_falha[idx_dem] = np.where(
                par_caiu, (tempo_missao_h - t_falha_par) / tempo_missao_h, 0.0
            )

        # Sem reparo, se falhou em algum momento em [0, T], permanece falhado em T.
        return falhou_par, falhou_par.copy(), fracao_falha

    # ---- Caso geral (com reparo e/ou espera morna): filtro vetorizado + DES exato
    t_b0 = (
        gerador.exponential(1.0 / taxa_falha_h, size=n_historias)
        if taxa_falha_h > 0.0
        else np.full(n_historias, np.inf)
    )
    if principal_parte_em_t0 and prob_demanda_partida > 0.0:
        falha_p0 = gerador.random(n_historias) < prob_demanda_partida
        t_b0 = np.where(falha_p0, 0.0, t_b0)

    t_b1 = (
        gerador.exponential(1.0 / taxa_espera, size=n_historias)
        if taxa_espera > 0.0
        else np.full(n_historias, np.inf)
    )

    t_primeiro = np.minimum(t_b0, t_b1)
    bomba_primeira = np.where(t_b0 <= t_b1, 0, 1)
    ativas = np.flatnonzero(t_primeiro < tempo_missao_h)

    falhou_missao = np.zeros(n_historias, dtype=bool)
    em_falha_fim = np.zeros(n_historias, dtype=bool)
    fracao_falha = np.zeros(n_historias, dtype=float)

    for idx in ativas:
        f_mis, f_fim, t_down = _des_uma_historia_par_bombas(
            t_falha_inicial=float(t_primeiro[idx]),
            bomba_inicial_falha=int(bomba_primeira[idx]),
            tempo_missao_h=tempo_missao_h,
            taxa_op=taxa_falha_h,
            taxa_espera=taxa_espera,
            prob_fts=prob_demanda_partida,
            mttr_h=mttr_h,
            n_equipes_reparo=n_equipes_reparo,
            gerador=gerador,
        )
        falhou_missao[idx] = f_mis
        em_falha_fim[idx] = f_fim
        fracao_falha[idx] = t_down / tempo_missao_h

    return falhou_missao, em_falha_fim, fracao_falha


def aplicar_standby_em_estados(
    estados: np.ndarray,
    eventos: list[str],
    parametros_mdp: ParametrosComponente,
    tempo_missao_h: float,
    gerador: np.random.Generator,
    mttr_h: float | None = None,
    fator_espera: float = 0.0,
    principal_parte_em_t0: bool = False,
    n_equipes_reparo: int = 1,
) -> np.ndarray:
    """Substitui os estados das bombas por pares em espera (standby) sem alterar a arvore.

    Na arvore de falhas ``BOMBAS_A = AND(MDP_A, MDP_C)`` e
    ``BOMBAS_B = AND(MDP_B, MDP_D)``. Para manter a mesma funcao estrutura,
    quando o par falha no modelo standby marcamos ambas as bombas do trem como
    ``True``; quando o par sobrevive, marcamos ambas como ``False``.
    """
    estados_mod = np.array(estados, dtype=bool, copy=True)
    n_historias = estados_mod.shape[0]
    indice = {ev: i for i, ev in enumerate(eventos)}

    for _, id_principal, id_reserva in PARES_BOMBAS:
        if id_principal in indice and id_reserva in indice:
            falhou_par, _, _ = simular_par_bombas_standby(
                taxa_falha_h=parametros_mdp.taxa_falha_h,
                prob_demanda_partida=parametros_mdp.prob_demanda,
                tempo_missao_h=tempo_missao_h,
                n_historias=n_historias,
                gerador=gerador,
                mttr_h=mttr_h,
                fator_espera=fator_espera,
                principal_parte_em_t0=principal_parte_em_t0,
                n_equipes_reparo=n_equipes_reparo,
            )
            estados_mod[:, indice[id_principal]] = falhou_par
            estados_mod[:, indice[id_reserva]] = falhou_par

    return estados_mod


# ------------------------------- motor DES do sistema completo com reparo
def simular_sistema_completo_des(
    arvore: mod_arvore.ArvoreDeFalhas,
    parametros_comp: dict[str, ParametrosComponente],
    tempo_missao_h: float,
    n_historias: int,
    semente: int,
    mttr_por_componente: dict[str, float] | None = None,
    fator_espera_bomba: float = 0.0,
    principal_parte_em_t0: bool = False,
    n_equipes_reparo_bomba: int = 1,
    nivel_confianca: float = 0.95,
) -> dict[str, float | int | str]:
    """Simula o sistema CCWS completo no tempo [0, T] com standby nas bombas e reparo.

    Cada evento nao-bomba alterna entre UP (taxa ``lambda_i``) e DOWN (reparo
    exponencial com media ``mttr_por_componente[comp]``, ou sem reparo se o
    componente nao estiver no dicionario), alem de possivel falha na demanda em
    ``t = 0`` (``prob_demanda``). Os pares de bombas ``(MDP_A, MDP_C)`` e
    ``(MDP_B, MDP_D)`` seguem a logica de bomba em espera + reparo.

    Usa filtro vetorizado inicial para pular historias em que nenhum evento
    ocorre em ``[0, T]``.
    """
    mttr_map = mttr_por_componente or {}
    eventos = arvore.lista_eventos_basicos()
    gerador = mc.preparar_gerador(semente)

    # Identifica eventos individuais (nao-bomba)
    bombas_ids = {b for _, p, r in PARES_BOMBAS for b in (p, r)}
    eventos_serie = [ev for ev in eventos if ev not in bombas_ids]

    comp_de = {ev: arvore.info_eventos_basicos[ev]["componente"] for ev in eventos}
    q_serie = np.array(
        [parametros_comp[comp_de[ev]].prob_demanda for ev in eventos_serie], dtype=float
    )
    lam_serie = np.array(
        [parametros_comp[comp_de[ev]].taxa_falha_h for ev in eventos_serie], dtype=float
    )
    mttr_serie = [mttr_map.get(comp_de[ev], None) for ev in eventos_serie]

    p_mdp = parametros_comp["MDP"]
    mttr_mdp = mttr_map.get("MDP", None)
    lam_mdp = p_mdp.taxa_falha_h
    lam_mdp_stby = lam_mdp * fator_espera_bomba

    # Sorteio exato da primeira falha em 1 passo vetorizado (sem vies de
    # condicionamento) para filtrar apenas historias em que ambos os trens
    # sofrem ao menos 1 evento em [0, T].
    n_serie = len(eventos_serie)
    t0_serie = np.full((n_historias, n_serie), np.inf, dtype=float)
    for j in range(n_serie):
        if lam_serie[j] > 0.0:
            t0_serie[:, j] = gerador.exponential(1.0 / lam_serie[j], size=n_historias)
        if q_serie[j] > 0.0:
            dem = gerador.random(n_historias) < q_serie[j]
            t0_serie[dem, j] = 0.0

    # Primeira falha dos 2 pares de bombas (trem A e trem B)
    t0_bomba_p = np.full((n_historias, len(PARES_BOMBAS)), np.inf, dtype=float)
    t0_bomba_r = np.full((n_historias, len(PARES_BOMBAS)), np.inf, dtype=float)
    for idx_par in range(len(PARES_BOMBAS)):
        if lam_mdp > 0.0:
            t0_bomba_p[:, idx_par] = gerador.exponential(1.0 / lam_mdp, size=n_historias)
        if principal_parte_em_t0 and p_mdp.prob_demanda > 0.0:
            dem = gerador.random(n_historias) < p_mdp.prob_demanda
            t0_bomba_p[dem, idx_par] = 0.0
        if lam_mdp_stby > 0.0:
            t0_bomba_r[:, idx_par] = gerador.exponential(
                1.0 / lam_mdp_stby, size=n_historias
            )

    min_serie = t0_serie.min(axis=1) if n_serie > 0 else np.full(n_historias, np.inf)
    min_bombas = np.minimum(t0_bomba_p.min(axis=1), t0_bomba_r.min(axis=1))
    # So ha chance de TOPO ocorrer se houver ao menos 1 evento em [0, T]
    # (na verdade so se AMBOS os trens tiverem >= 1 evento em [0, T]!).
    trem_de_serie = [arvore.info_eventos_basicos[ev]["trem"] for ev in eventos_serie]
    idx_a = [j for j, tr in enumerate(trem_de_serie) if tr == "A"]
    idx_b = [j for j, tr in enumerate(trem_de_serie) if tr == "B"]

    tem_ev_a = (t0_serie[:, idx_a].min(axis=1) < tempo_missao_h) | (
        np.minimum(t0_bomba_p[:, 0], t0_bomba_r[:, 0]) < tempo_missao_h
    )
    tem_ev_b = (t0_serie[:, idx_b].min(axis=1) < tempo_missao_h) | (
        np.minimum(t0_bomba_p[:, 1], t0_bomba_r[:, 1]) < tempo_missao_h
    )
    candidatas = np.flatnonzero(tem_ev_a & tem_ev_b)

    n_falhas_missao = 0
    n_em_falha_fim = 0
    soma_fracao_falha = 0.0
    soma_fracao_falha_q2 = 0.0

    for h in candidatas:
        f_mis, f_fim, t_down = _des_uma_historia_sistema(
            arvore=arvore,
            eventos_serie=eventos_serie,
            t0_serie_h=t0_serie[h],
            lam_serie=lam_serie,
            mttr_serie=mttr_serie,
            t0_bomba_p_h=t0_bomba_p[h],
            t0_bomba_r_h=t0_bomba_r[h],
            lam_mdp=lam_mdp,
            lam_mdp_stby=lam_mdp_stby,
            q_fts_mdp=p_mdp.prob_demanda,
            mttr_mdp=mttr_mdp,
            n_equipes_bomba=n_equipes_reparo_bomba,
            tempo_missao_h=tempo_missao_h,
            gerador=gerador,
        )
        if f_mis:
            n_falhas_missao += 1
        if f_fim:
            n_em_falha_fim += 1
        frac = t_down / tempo_missao_h
        soma_fracao_falha += frac
        soma_fracao_falha_q2 += frac * frac

    est_f = mc.estimar_estatisticas_binomiais(
        n_falhas=n_falhas_missao,
        n_historias=n_historias,
        nivel_confianca=nivel_confianca,
    )
    est_u = mc.estimar_estatisticas_binomiais(
        n_falhas=n_em_falha_fim,
        n_historias=n_historias,
        nivel_confianca=nivel_confianca,
    )
    u_media = soma_fracao_falha / n_historias
    var_u = max(0.0, (soma_fracao_falha_q2 / n_historias) - u_media * u_media)
    se_u_media = math.sqrt(var_u / n_historias)

    return {
        "modelo": "standby_com_reparo_des" if mttr_map else "standby_sem_reparo_des",
        "n_historias": n_historias,
        "tempo_missao_h": tempo_missao_h,
        "semente": semente,
        "n_falhas_missao": n_falhas_missao,
        "p_topo_missao": est_f["p_topo"],
        "erro_padrao_missao": est_f["erro_padrao"],
        "ic95_missao_inf": est_f["ic_wilson_inf"],
        "ic95_missao_sup": est_f["ic_wilson_sup"],
        "indisponibilidade_pontual_T": est_u["p_topo"],
        "ic95_u_pontual_inf": est_u["ic_wilson_inf"],
        "ic95_u_pontual_sup": est_u["ic_wilson_sup"],
        "indisponibilidade_media": u_media,
        "erro_padrao_u_media": se_u_media,
    }


def _des_uma_historia_sistema(
    arvore: mod_arvore.ArvoreDeFalhas,
    eventos_serie: list[str],
    t0_serie_h: np.ndarray,
    lam_serie: np.ndarray,
    mttr_serie: list[float | None],
    t0_bomba_p_h: np.ndarray,
    t0_bomba_r_h: np.ndarray,
    lam_mdp: float,
    lam_mdp_stby: float,
    q_fts_mdp: float,
    mttr_mdp: float | None,
    n_equipes_bomba: int,
    tempo_missao_h: float,
    gerador: np.random.Generator,
) -> tuple[bool, bool, float]:
    """DES exato de 1 historia do CCWS completo (20 eventos serie + 2 pares standby)."""
    estados_arvore: dict[str, bool] = {ev: False for ev in arvore.lista_eventos_basicos()}
    # Fila de eventos: (tempo, categoria, id_item, acao, versao)
    fila: list[tuple[float, str, int, str, int]] = []

    # 1. Inicializa eventos serie
    for j, ev in enumerate(eventos_serie):
        t_ev = float(t0_serie_h[j])
        if t_ev == 0.0:
            estados_arvore[ev] = True
            mttr = mttr_serie[j]
            if mttr is not None:
                t_rep = float(gerador.exponential(mttr))
                if t_rep < tempo_missao_h:
                    heapq.heappush(fila, (t_rep, "SERIE", j, "REPARO", 0))
        elif t_ev < tempo_missao_h:
            heapq.heappush(fila, (t_ev, "SERIE", j, "FALHA", 0))

    # 2. Inicializa os dois pares de bombas standby (par 0 = Trem A, par 1 = Trem B)
    est_bombas = [["OP", "STBY"], ["OP", "STBY"]]
    ver_bombas = [[0, 0], [0, 0]]
    em_rep_par = [0, 0]

    def agendar_bomba(tempo: float, par: int, b: int, acao: str) -> None:
        if tempo < tempo_missao_h:
            ver_bombas[par][b] += 1
            heapq.heappush(fila, (tempo, "BOMBA", par * 2 + b, acao, ver_bombas[par][b]))

    def falhar_bomba(t_cur: float, par: int, b: int) -> None:
        if mttr_mdp is None:
            est_bombas[par][b] = "FAIL"
        elif em_rep_par[par] < n_equipes_bomba:
            est_bombas[par][b] = "REP"
            em_rep_par[par] += 1
            agendar_bomba(t_cur + float(gerador.exponential(mttr_mdp)), par, b, "REPARO")
        else:
            est_bombas[par][b] = "FAIL"

    def promover_bomba(t_cur: float, par: int) -> None:
        if "OP" in est_bombas[par]:
            return
        for b in (0, 1):
            if est_bombas[par][b] == "STBY":
                ver_bombas[par][b] += 1
                if q_fts_mdp > 0.0 and gerador.random() < q_fts_mdp:
                    falhar_bomba(t_cur, par, b)
                else:
                    est_bombas[par][b] = "OP"
                    if lam_mdp > 0.0:
                        agendar_bomba(
                            t_cur + float(gerador.exponential(1.0 / lam_mdp)),
                            par,
                            b,
                            "FALHA",
                        )
                return

    def sincronizar_par_arvore(par: int) -> None:
        _, id_p, id_r = PARES_BOMBAS[par]
        par_down = "OP" not in est_bombas[par]
        estados_arvore[id_p] = par_down
        estados_arvore[id_r] = par_down

    for par in range(len(PARES_BOMBAS)):
        tp = float(t0_bomba_p_h[par])
        tr = float(t0_bomba_r_h[par])
        if tp == 0.0:
            falhar_bomba(0.0, par, 0)
            promover_bomba(0.0, par)
        else:
            if tp < tempo_missao_h:
                agendar_bomba(tp, par, 0, "FALHA")
            if tr < tempo_missao_h:
                agendar_bomba(tr, par, 1, "FALHA")
        sincronizar_par_arvore(par)

    t_atual = 0.0
    topo_down = arvore.avalia(estados_arvore)
    falhou_na_missao = topo_down
    tempo_em_falha = 0.0

    while fila:
        t_ev, cat, item, acao, v_ev = heapq.heappop(fila)
        if cat == "BOMBA":
            par, b = divmod(item, 2)
            if v_ev != ver_bombas[par][b]:
                continue

        if topo_down:
            tempo_em_falha += t_ev - t_atual
        t_atual = t_ev

        if cat == "SERIE":
            ev = eventos_serie[item]
            if acao == "FALHA":
                estados_arvore[ev] = True
                mttr = mttr_serie[item]
                if mttr is not None:
                    t_rep = t_atual + float(gerador.exponential(mttr))
                    if t_rep < tempo_missao_h:
                        heapq.heappush(fila, (t_rep, "SERIE", item, "REPARO", 0))
            else:  # REPARO
                estados_arvore[ev] = False
                if lam_serie[item] > 0.0:
                    t_f = t_atual + float(gerador.exponential(1.0 / lam_serie[item]))
                    if t_f < tempo_missao_h:
                        heapq.heappush(fila, (t_f, "SERIE", item, "FALHA", 0))
        else:  # BOMBA
            par, b = divmod(item, 2)
            if acao == "FALHA":
                falhar_bomba(t_atual, par, b)
                promover_bomba(t_atual, par)
            else:  # REPARO
                em_rep_par[par] -= 1
                outra = 1 - b
                if (
                    est_bombas[par][outra] == "FAIL"
                    and mttr_mdp is not None
                    and em_rep_par[par] < n_equipes_bomba
                ):
                    est_bombas[par][outra] = "REP"
                    em_rep_par[par] += 1
                    agendar_bomba(
                        t_atual + float(gerador.exponential(mttr_mdp)),
                        par,
                        outra,
                        "REPARO",
                    )
                if "OP" not in est_bombas[par]:
                    est_bombas[par][b] = "OP"
                    if lam_mdp > 0.0:
                        agendar_bomba(
                            t_atual + float(gerador.exponential(1.0 / lam_mdp)),
                            par,
                            b,
                            "FALHA",
                        )
                else:
                    est_bombas[par][b] = "STBY"
                    if lam_mdp_stby > 0.0:
                        agendar_bomba(
                            t_atual + float(gerador.exponential(1.0 / lam_mdp_stby)),
                            par,
                            b,
                            "FALHA",
                        )
            sincronizar_par_arvore(par)

        topo_down = arvore.avalia(estados_arvore)
        if topo_down:
            falhou_na_missao = True

    if topo_down:
        tempo_em_falha += tempo_missao_h - t_atual

    return falhou_na_missao, topo_down, tempo_em_falha


# -------------------------------------------- comparacoes de subsistema e topo
def comparar_modelos_bombas(
    parametros_mdp: ParametrosComponente,
    horizontes_h: Sequence[float],
    n_historias: int,
    semente: int,
    mttr_mdp_h: float | None = None,
) -> pd.DataFrame:
    """Compara modelos do subsistema BOMBAS_A (1+1 bombas) em varios horizontes."""
    linhas: list[dict[str, float | int | str | None]] = []

    for idx_h, T in enumerate(horizontes_h):
        p_ativa_exata = parametros_mdp.prob_missao_estatica(T) ** 2
        p_stby_t0_exata = prob_falha_standby_analitica(
            parametros_mdp.taxa_falha_h, parametros_mdp.prob_demanda, T, True
        )
        p_stby_op_exata = prob_falha_standby_analitica(
            parametros_mdp.taxa_falha_h, parametros_mdp.prob_demanda, T, False
        )

        # 1. Redundancia ativa (sem reparo)
        g_at = mc.preparar_gerador(semente + 100 * idx_h + 1)
        p1 = parametros_mdp.prob_missao_estatica(T)
        falhas_at = (g_at.random(n_historias) < p1) & (g_at.random(n_historias) < p1)
        est_at = mc.estimar_probabilidade_topo(falhas_at)
        linhas.append(
            {
                "horizonte_h": T,
                "modelo_bombas": "redundancia_ativa_sem_reparo",
                "mttr_h": np.nan,
                "n_historias": n_historias,
                "n_falhas": est_at["n_falhas"],
                "p_falha_mc": est_at["p_topo"],
                "ic95_inf": est_at["ic_wilson_inf"],
                "ic95_sup": est_at["ic_wilson_sup"],
                "p_analitica_ref": p_ativa_exata,
                "indisponibilidade_media": np.nan,
            }
        )

        # 2. Cold standby (principal parte em t=0, sem reparo)
        g_s1 = mc.preparar_gerador(semente + 100 * idx_h + 2)
        f_s1, _, u_s1 = simular_par_bombas_standby(
            taxa_falha_h=parametros_mdp.taxa_falha_h,
            prob_demanda_partida=parametros_mdp.prob_demanda,
            tempo_missao_h=T,
            n_historias=n_historias,
            gerador=g_s1,
            mttr_h=None,
            principal_parte_em_t0=True,
        )
        est_s1 = mc.estimar_probabilidade_topo(f_s1)
        linhas.append(
            {
                "horizonte_h": T,
                "modelo_bombas": "cold_standby_principal_parte_t0",
                "mttr_h": np.nan,
                "n_historias": n_historias,
                "n_falhas": est_s1["n_falhas"],
                "p_falha_mc": est_s1["p_topo"],
                "ic95_inf": est_s1["ic_wilson_inf"],
                "ic95_sup": est_s1["ic_wilson_sup"],
                "p_analitica_ref": p_stby_t0_exata,
                "indisponibilidade_media": float(np.mean(u_s1)),
            }
        )

        # 3. Cold standby (principal ja em operacao continua NR, sem reparo)
        g_s2 = mc.preparar_gerador(semente + 100 * idx_h + 3)
        f_s2, _, u_s2 = simular_par_bombas_standby(
            taxa_falha_h=parametros_mdp.taxa_falha_h,
            prob_demanda_partida=parametros_mdp.prob_demanda,
            tempo_missao_h=T,
            n_historias=n_historias,
            gerador=g_s2,
            mttr_h=None,
            principal_parte_em_t0=False,
        )
        est_s2 = mc.estimar_probabilidade_topo(f_s2)
        linhas.append(
            {
                "horizonte_h": T,
                "modelo_bombas": "cold_standby_principal_operando",
                "mttr_h": np.nan,
                "n_historias": n_historias,
                "n_falhas": est_s2["n_falhas"],
                "p_falha_mc": est_s2["p_topo"],
                "ic95_inf": est_s2["ic_wilson_inf"],
                "ic95_sup": est_s2["ic_wilson_sup"],
                "p_analitica_ref": p_stby_op_exata,
                "indisponibilidade_media": float(np.mean(u_s2)),
            }
        )

        # 4. Cold standby COM reparo (executado apenas se MTTR documentado foi fornecido)
        if mttr_mdp_h is not None:
            g_sr = mc.preparar_gerador(semente + 100 * idx_h + 4)
            f_sr, _, u_sr = simular_par_bombas_standby(
                taxa_falha_h=parametros_mdp.taxa_falha_h,
                prob_demanda_partida=parametros_mdp.prob_demanda,
                tempo_missao_h=T,
                n_historias=n_historias,
                gerador=g_sr,
                mttr_h=mttr_mdp_h,
                principal_parte_em_t0=False,
            )
            est_sr = mc.estimar_probabilidade_topo(f_sr)
            linhas.append(
                {
                    "horizonte_h": T,
                    "modelo_bombas": "cold_standby_com_reparo",
                    "mttr_h": mttr_mdp_h,
                    "n_historias": n_historias,
                    "n_falhas": est_sr["n_falhas"],
                    "p_falha_mc": est_sr["p_topo"],
                    "ic95_inf": est_sr["ic_wilson_inf"],
                    "ic95_sup": est_sr["ic_wilson_sup"],
                    "p_analitica_ref": np.nan,
                    "indisponibilidade_media": float(np.mean(u_sr)),
                }
            )

    return pd.DataFrame(linhas)


def rodar_topo_com_standby(
    arvore: mod_arvore.ArvoreDeFalhas,
    probabilidades: dict[str, float],
    parametros_mdp: ParametrosComponente,
    tempo_missao_h: float,
    n_historias: int,
    semente: int,
    mttr_mdp_h: float | None = None,
    principal_parte_em_t0: bool = False,
    tamanho_lote: int = mc.TAMANHO_LOTE_PADRAO,
    nivel_confianca: float = 0.95,
) -> dict[str, float | int | str]:
    """Roda o CCWS completo substituindo apenas o subsistema de bombas por standby."""
    eventos = arvore.lista_eventos_basicos()
    gerador_eventos = mc.preparar_gerador(semente)
    gerador_bombas = mc.preparar_gerador(semente + 1)

    n_falhas_total = 0
    restante = int(n_historias)
    while restante > 0:
        n_lote = min(tamanho_lote, restante)
        estados_lote = mc.sortear_estados(eventos, probabilidades, gerador_eventos, n_lote)
        estados_lote = aplicar_standby_em_estados(
            estados=estados_lote,
            eventos=eventos,
            parametros_mdp=parametros_mdp,
            tempo_missao_h=tempo_missao_h,
            gerador=gerador_bombas,
            mttr_h=mttr_mdp_h,
            principal_parte_em_t0=principal_parte_em_t0,
        )
        falhas_lote = mc.avaliar_historias(arvore, eventos, estados_lote)
        n_falhas_total += int(np.count_nonzero(falhas_lote))
        restante -= n_lote

    nome_modelo = (
        "standby_principal_parte_t0"
        if principal_parte_em_t0
        else "standby_principal_operando"
    )
    if mttr_mdp_h is not None:
        nome_modelo += "_com_reparo"

    return {
        "modelo": nome_modelo,
        **mc.estimar_estatisticas_binomiais(
            n_falhas=n_falhas_total,
            n_historias=int(n_historias),
            nivel_confianca=nivel_confianca,
        ),
        "mttr_mdp_h": mttr_mdp_h if mttr_mdp_h is not None else np.nan,
        "tempo_missao_h": tempo_missao_h,
        "semente": int(semente),
    }


def grafico_bombas(df_bombas: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva o grafico comparativo Ativa x Cold Standby em ``monte_carlo/resultados/``."""
    destino = (
        Path(caminho)
        if caminho is not None
        else PASTA_RESULTADOS / "mc_dinamico_bombas.png"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)

    modelos = [
        ("redundancia_ativa_sem_reparo", "Redundância ativa", "#1F4E79"),
        ("cold_standby_principal_parte_t0", "Cold standby\n(principal parte em t=0)", "#E07A2B"),
        ("cold_standby_principal_operando", "Cold standby\n(principal já operando)", "#2E7D32"),
    ]
    horizontes = sorted(df_bombas["horizonte_h"].unique())
    rotulos_h = [
        "24 h\n(missão base)" if h == 24.0
        else ("720 h\n(30 dias)" if h == 720.0
              else ("8.760 h\n(1 ano)" if h == 8760.0 else f"{h:g} h"))
        for h in horizontes
    ]

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(11.5, 4.9), gridspec_kw={"width_ratios": [1.35, 1.0]}
    )

    x = np.arange(len(horizontes))
    largura = 0.25

    for idx_m, (chave, rotulo, cor) in enumerate(modelos):
        sub = df_bombas[df_bombas["modelo_bombas"] == chave].set_index("horizonte_h")
        vals_ref = [float(sub.loc[h, "p_analitica_ref"]) for h in horizontes]
        vals_mc = [float(sub.loc[h, "p_falha_mc"]) for h in horizontes]
        n_falhas = [int(sub.loc[h, "n_falhas"]) for h in horizontes]

        pos = x + (idx_m - 1) * largura
        ax1.bar(
            pos,
            vals_ref,
            width=largura * 0.9,
            color=cor,
            alpha=0.82,
            edgecolor="#222222",
            linewidth=0.6,
            label=rotulo.replace("\n", " "),
        )
        for px, pmc, kf in zip(pos, vals_mc, n_falhas):
            if kf > 0:
                ax1.scatter(
                    [px], [pmc], color="white", edgecolor="#111111",
                    s=36, zorder=5, linewidth=1.1,
                )

    ax1.scatter(
        [], [], color="white", edgecolor="#111111", s=36, linewidth=1.1,
        label="Estimativa MC (quando k > 0)",
    )
    if 24.0 in horizontes:
        i24 = horizontes.index(24.0)
        ax1.annotate(
            "~11× menor",
            xy=(i24 + largura, 2.35e-8),
            xytext=(i24 + largura + 0.14, 1.3e-7),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color="#1B5E20",
            arrowprops=dict(arrowstyle="->", color="#1B5E20", lw=1.1),
        )
    if 8760.0 in horizontes:
        i1y = horizontes.index(8760.0)
        ax1.annotate(
            "~2× menor",
            xy=(i1y + largura, 1.57e-4),
            xytext=(i1y + largura, 6.0e-4),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color="#1B5E20",
            arrowprops=dict(arrowstyle="->", color="#1B5E20", lw=1.0),
        )

    ax1.set_yscale("log")
    ax1.set_ylim(2e-9, 2e-3)
    ax1.set_xticks(x)
    ax1.set_xticklabels(rotulos_h)
    ax1.set_ylabel(r"Probabilidade de falha de $\mathrm{BOMBAS\_A}$")
    ax1.set_title("Subsistema BOMBAS_A em três horizontes (sem reparo)")
    ax1.grid(True, axis="y", which="both", linestyle=":", alpha=0.55)
    ax1.legend(loc="upper left", fontsize=8.0, frameon=True)

    # Painel direito: maior horizonte disponivel (escala linear com IC 95% Wilson)
    h_max = horizontes[-1]
    sub_max = df_bombas[df_bombas["horizonte_h"] == h_max].set_index("modelo_bombas")
    x2 = np.arange(len(modelos))
    p_mc = [float(sub_max.loc[k, "p_falha_mc"]) for k, _, _ in modelos]
    p_ref = [float(sub_max.loc[k, "p_analitica_ref"]) for k, _, _ in modelos]
    err_inf = [float(sub_max.loc[k, "p_falha_mc"] - sub_max.loc[k, "ic95_inf"]) for k, _, _ in modelos]
    err_sup = [float(sub_max.loc[k, "ic95_sup"] - sub_max.loc[k, "p_falha_mc"]) for k, _, _ in modelos]
    falhas_max = [int(sub_max.loc[k, "n_falhas"]) for k, _, _ in modelos]
    cores2 = [c for _, _, c in modelos]

    ax2.bar(
        x2, p_mc, width=0.52, color=cores2, alpha=0.78, edgecolor="#222222",
        linewidth=0.7, yerr=[err_inf, err_sup], capsize=5,
        error_kw={"elinewidth": 1.3, "ecolor": "#222222"},
        label="Monte Carlo + IC 95% Wilson",
    )
    ax2.scatter(
        x2, p_ref, marker="D", s=48, color="#D62728", edgecolor="white",
        linewidth=0.8, zorder=6, label="Referência analítica fechada",
    )
    ymax2 = max(max(p + s for p, s in zip(p_mc, err_sup)), max(p_ref)) * 1.28
    for xi, pmc, esup, kf in zip(x2, p_mc, err_sup, falhas_max):
        ax2.text(
            xi, pmc + esup + ymax2 * 0.025, f"k = {kf}\n({pmc:.2E})",
            ha="center", va="bottom", fontsize=8.2,
        )

    ax2.set_xticks(x2)
    ax2.set_xticklabels([r for _, r, _ in modelos], fontsize=8.3)
    ax2.set_ylim(0, ymax2)
    ax2.ticklabel_format(axis="y", style="sci", scilimits=(-2, 3))
    ax2.set_ylabel(rf"$P(\mathrm{{BOMBAS\_A}})$ em {h_max:,.0f} h")
    ax2.set_title(f"Validação MC vs. Analítico em {h_max:,.0f} h")
    ax2.grid(True, axis="y", linestyle=":", alpha=0.55)
    ax2.legend(loc="upper right", fontsize=8.0, frameon=True)

    fig.tight_layout()
    fig.savefig(destino, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return destino


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulacao dinamica de Monte Carlo (bomba em espera e reparo)."
    )
    parser.add_argument(
        "--mttr-csv",
        type=Path,
        default=None,
        help=(
            "CSV opcional com MTTRs documentados (colunas: componente, mttr_h, "
            "fonte, pagina_tabela). Se omitido, roda sem reparo (nenhum MTTR "
            "e inventado)."
        ),
    )
    parser.add_argument(
        "--n-bombas",
        type=int,
        default=None,
        help="Historias para a comparacao do subsistema BOMBAS_A (padrao: n_simulacoes).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Executa a comparacao dinamica (standby e, se MTTR fornecido, reparo DES)."""
    args = _parse_args(argv)

    config = mod_dados.carregar_config()
    arvore = mod_arvore.carregar_arvore()
    parametros_csv = mod_dados.carregar_parametros_eventos()
    probs_base = mc.extrair_probabilidades_missao(
        parametros_csv, arvore.lista_eventos_basicos()
    )
    params_comp = carregar_parametros_decompostos()
    p_mdp = params_comp["MDP"]

    mttr_map = carregar_mttr_csv(args.mttr_csv) if args.mttr_csv is not None else {}
    mttr_mdp = mttr_map.get("MDP", None)

    t_missao = float(config["tempo_missao_h"])
    n_sim = int(config["n_simulacoes"])
    semente = int(config["semente_aleatoria"])
    n_bombas = int(args.n_bombas) if args.n_bombas is not None else n_sim

    # 1. Comparacao focada no subsistema BOMBAS_A em 24 h (missao), 720 h (30 d) e 8760 h (1 ano)
    horizontes = [t_missao, 720.0, 8760.0]
    df_bombas = comparar_modelos_bombas(
        parametros_mdp=p_mdp,
        horizontes_h=horizontes,
        n_historias=n_bombas,
        semente=semente,
        mttr_mdp_h=mttr_mdp,
    )

    # 2. Comparacao no evento topo (T = tempo_missao_h)
    res_ativa, _ = mc.rodar_simulacao_base(
        arvore=arvore,
        probabilidades=probs_base,
        n_historias=n_sim,
        semente=semente,
    )
    res_ativa["mttr_mdp_h"] = np.nan
    res_ativa["tempo_missao_h"] = t_missao

    res_stby_op = rodar_topo_com_standby(
        arvore=arvore,
        probabilidades=probs_base,
        parametros_mdp=p_mdp,
        tempo_missao_h=t_missao,
        n_historias=n_sim,
        semente=semente,
        mttr_mdp_h=mttr_mdp,
        principal_parte_em_t0=False,
    )
    res_stby_t0 = rodar_topo_com_standby(
        arvore=arvore,
        probabilidades=probs_base,
        parametros_mdp=p_mdp,
        tempo_missao_h=t_missao,
        n_historias=n_sim,
        semente=semente,
        mttr_mdp_h=mttr_mdp,
        principal_parte_em_t0=True,
    )
    df_topo = pd.DataFrame([res_ativa, res_stby_op, res_stby_t0])

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    arq_bombas = PASTA_RESULTADOS / "mc_dinamico_bombas.csv"
    arq_topo = PASTA_RESULTADOS / "mc_dinamico_topo.csv"
    df_bombas.to_csv(arq_bombas, index=False)
    df_topo.to_csv(arq_topo, index=False)
    arq_png = grafico_bombas(df_bombas)

    print("=" * 76)
    print("Frente 4 - Simulacao Dinamica (Bomba em Espera / Standby e Reparo DES)")
    print("=" * 76)
    print(
        f"MDP (INL Table 1): q_FTS = {p_mdp.prob_demanda:.3E}, "
        f"lambda_op = {p_mdp.taxa_falha_h:.4E} 1/h"
    )
    if mttr_map:
        print(f"MTTR carregado de {args.mttr_csv}: {mttr_map}")
    else:
        print(
            "MTTR: nao fornecido (em branco por regra do projeto — nenhum dado "
            "inventado; use --mttr-csv quando houver fonte documentada)."
        )
    print("-" * 76)
    print("Subsistema BOMBAS_A (1+1 bombas):")
    cols_b = [
        "horizonte_h",
        "modelo_bombas",
        "n_falhas",
        "p_falha_mc",
        "p_analitica_ref",
    ]
    print(df_bombas[cols_b].to_string(index=False))
    print("-" * 76)
    print(f"Evento TOPO (T = {t_missao:g} h, N = {n_sim:,}):")
    cols_t = ["modelo", "n_falhas", "p_topo", "ic95_inf", "ic95_sup"]
    print(df_topo[cols_t].to_string(index=False))
    print("-" * 76)
    print(f"Salvo em: {arq_bombas}")
    print(f"Salvo em: {arq_topo}")
    print(f"Grafico:  {arq_png}")
    print("=" * 76)


if __name__ == "__main__":
    main()

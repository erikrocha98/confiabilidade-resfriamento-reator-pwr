"""Frente 4 - Simulacao de Monte Carlo da arvore de falhas do CCWS.

Implementa o nucleo da simulacao de Monte Carlo para estimar a probabilidade
do evento topo (perda da funcao de resfriamento do CCWS):

- Le a configuracao global (``n_simulacoes``, ``semente_aleatoria``,
  ``tempo_missao_h``) via ``ccws.dados`` e a arvore via ``ccws.arvore``.
- Modelo base (Fase 1 - redundancia ativa / estatico):
    1. sorteia o estado (falhou / nao falhou) dos 24 eventos basicos a partir
       de ``prob_missao`` em ``dados/parametros_eventos.csv``, processando em
       lotes vetorizados para suportar dezenas de milhoes de historias sem
       esgotar memoria;
    2. avalia a funcao estrutura genericamente a partir de ``arvore.portas``
       (equivalencia validada contra ``ccws.arvore.ArvoreDeFalhas.avalia``);
    3. calcula a estimativa pontual, erro padrao, erro relativo e intervalos de
       confianca (Wald, Wilson e Clopper-Pearson) e a contribuicao empirica dos
       eventos basicos (aproximacao de Fussell-Vesely por Monte Carlo).
- Extensao dinamica (Fase 3 - bomba em espera / standby e reparo):
    reservada para o ponto de extensao ``tratar_bomba_reserva`` / modulo
    dinamico (nao implementado nesta fase; nenhum dado de MTTR e inventado).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Permite rodar o script diretamente (ex.: python monte_carlo/simulacao.py).
RAIZ_REPO = Path(__file__).resolve().parent.parent
if str(RAIZ_REPO) not in sys.path:
    sys.path.insert(0, str(RAIZ_REPO))

from ccws import arvore as mod_arvore  # noqa: E402
from ccws import dados as mod_dados  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
TAMANHO_LOTE_PADRAO = 500_000


def preparar_gerador(semente: int) -> np.random.Generator:
    """Cria o gerador de numeros aleatorios com semente fixa (reprodutibilidade)."""
    return np.random.default_rng(int(semente))


def extrair_probabilidades_missao(
    parametros: pd.DataFrame, eventos: list[str]
) -> dict[str, float]:
    """Extrai ``{id_evento: prob_missao}`` validando cobertura completa da arvore."""
    if parametros.empty:
        raise mod_dados.ErroDados(
            "dados/parametros_eventos.csv esta vazio; preencha os parametros (frente 2)."
        )

    tabela = parametros.dropna(subset=["id_evento"]).set_index("id_evento")
    faltantes: list[str] = []
    probabilidades: dict[str, float] = {}

    for id_evento in eventos:
        if id_evento not in tabela.index or pd.isna(tabela.loc[id_evento, "prob_missao"]):
            faltantes.append(id_evento)
            continue
        p = float(tabela.loc[id_evento, "prob_missao"])
        if not (0.0 <= p <= 1.0):
            raise mod_dados.ErroDados(
                f"prob_missao fora de [0, 1] para '{id_evento}': {p}"
            )
        probabilidades[id_evento] = p

    if faltantes:
        raise mod_dados.ErroDados(
            "eventos basicos sem prob_missao preenchida: " + ", ".join(faltantes)
        )

    return probabilidades


def sortear_estados(
    eventos: list[str],
    probabilidades: dict[str, float],
    gerador: np.random.Generator,
    n_historias: int,
) -> np.ndarray:
    """Sorteia a matriz de estados dos eventos basicos (Bernoulli vetorizado).

    Args:
        eventos: lista ordenada de ids dos eventos basicos.
        probabilidades: dicionario ``{id_evento: probabilidade_de_falha}``.
        gerador: instancia de ``np.random.Generator``.
        n_historias: numero de historias (linhas) a sortear.

    Returns:
        Array booleano de forma ``(n_historias, len(eventos))``, ``True`` = falhou.
    """
    if n_historias <= 0:
        raise ValueError(f"n_historias deve ser positivo, recebido: {n_historias}")

    faltantes = [ev for ev in eventos if ev not in probabilidades]
    if faltantes:
        raise KeyError("probabilidade ausente para eventos: " + ", ".join(faltantes))

    estados = np.empty((n_historias, len(eventos)), dtype=bool)
    for idx, id_evento in enumerate(eventos):
        p = float(probabilidades[id_evento])
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"probabilidade fora de [0, 1] para '{id_evento}': {p}")
        estados[:, idx] = gerador.random(n_historias) < p

    return estados


def avaliar_historias(
    arvore: mod_arvore.ArvoreDeFalhas,
    eventos: list[str],
    estados: np.ndarray,
) -> np.ndarray:
    """Avalia a funcao estrutura da arvore de forma vetorizada em cada historia.

    Percorre genericamente ``arvore.portas`` usando operacoes booleanas NumPy
    (``&`` para AND, ``|`` para OR), produzindo resultado identico a
    ``ccws.arvore.ArvoreDeFalhas.avalia``.

    Args:
        arvore: arvore de falhas carregada via ``ccws.arvore``.
        eventos: lista de ids correspondentes as colunas de ``estados``.
        estados: array booleano ``(n_historias, len(eventos))``, ``True`` = falhou.

    Returns:
        Array booleano de tamanho ``n_historias``, ``True`` = evento topo ocorreu.
    """
    estados_bool = np.asarray(estados, dtype=bool)
    if estados_bool.ndim != 2:
        raise ValueError(
            f"estados deve ser um array 2D (n_historias, n_eventos), forma: {estados_bool.shape}"
        )
    if estados_bool.shape[1] != len(eventos):
        raise ValueError(
            f"numero de colunas de estados ({estados_bool.shape[1]}) difere de "
            f"len(eventos) ({len(eventos)})"
        )

    desconhecidos = sorted(set(eventos) - set(arvore.info_eventos_basicos))
    if desconhecidos:
        raise mod_arvore.ErroArvore(
            "estados informados para eventos que nao existem na arvore: "
            + ", ".join(desconhecidos)
        )

    n_historias = estados_bool.shape[0]
    indice_por_evento = {ev: i for i, ev in enumerate(eventos)}
    cache: dict[str, np.ndarray] = {}

    def _avalia_no(id_no: str) -> np.ndarray:
        if id_no in cache:
            return cache[id_no]

        if id_no in arvore.info_eventos_basicos:
            if id_no in indice_por_evento:
                resultado = estados_bool[:, indice_por_evento[id_no]]
            else:
                resultado = np.zeros(n_historias, dtype=bool)
            cache[id_no] = resultado
            return resultado

        porta = arvore.portas[id_no]
        entradas = porta["entradas"]
        resultado = _avalia_no(entradas[0]).copy()
        if porta["tipo"] == "AND":
            for entrada in entradas[1:]:
                resultado &= _avalia_no(entrada)
        else:  # OR
            for entrada in entradas[1:]:
                resultado |= _avalia_no(entrada)

        cache[id_no] = resultado
        return resultado

    return _avalia_no(arvore.evento_topo).copy()


def estimar_estatisticas_binomiais(
    n_falhas: int,
    n_historias: int,
    nivel_confianca: float = 0.95,
) -> dict[str, float]:
    """Calcula estimativa pontual, erro padrao e ICs (Wald, Wilson, Clopper-Pearson).

    Para eventos raros (como o topo do CCWS, ~1e-5), o intervalo de Wald
    (normal) perde cobertura quando o numero de falhas observadas e pequeno.
    Por isso ``ic95_inf`` / ``ic95_sup`` (ou para o nivel informado) adotam o
    intervalo de **Wilson** como padrao, mantendo tambem Wald e Clopper-Pearson
    (exato binomial) explicitos para comparacao no relatorio.
    """
    if n_historias <= 0:
        raise ValueError(f"n_historias deve ser positivo, recebido: {n_historias}")
    if not (0 <= n_falhas <= n_historias):
        raise ValueError(
            f"n_falhas ({n_falhas}) deve estar entre 0 e n_historias ({n_historias})"
        )
    if not (0.0 < nivel_confianca < 1.0):
        raise ValueError(
            f"nivel_confianca deve estar em (0, 1), recebido: {nivel_confianca}"
        )

    k = int(n_falhas)
    n = int(n_historias)
    alpha = 1.0 - nivel_confianca
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))

    p = k / n
    se = math.sqrt(p * (1.0 - p) / n)
    erro_relativo = (se / p) if k > 0 else float("nan")

    # 1. Intervalo de Wald (aproximacao normal classica)
    ic_wald_inf = max(0.0, p - z * se)
    ic_wald_sup = min(1.0, p + z * se)

    # 2. Intervalo de Wilson (escore; robusto para eventos raros)
    z2_n = (z * z) / n
    denom = 1.0 + z2_n
    centro = (p + 0.5 * z2_n) / denom
    meia_wilson = (z / denom) * math.sqrt((p * (1.0 - p) + 0.25 * z2_n) / n)
    ic_wilson_inf = 0.0 if k == 0 else max(0.0, centro - meia_wilson)
    ic_wilson_sup = 1.0 if k == n else min(1.0, centro + meia_wilson)

    # 3. Intervalo exato binomial de Clopper-Pearson
    ic_cp_inf = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    ic_cp_sup = 1.0 if k == n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))

    return {
        "n_historias": n,
        "n_falhas": k,
        "p_topo": p,
        "erro_padrao": se,
        "erro_relativo": erro_relativo,
        "nivel_confianca": nivel_confianca,
        "ic95_inf": ic_wilson_inf,
        "ic95_sup": ic_wilson_sup,
        "ic_wald_inf": ic_wald_inf,
        "ic_wald_sup": ic_wald_sup,
        "ic_wilson_inf": ic_wilson_inf,
        "ic_wilson_sup": ic_wilson_sup,
        "ic_clopper_pearson_inf": ic_cp_inf,
        "ic_clopper_pearson_sup": ic_cp_sup,
    }


def estimar_probabilidade_topo(
    falhas_topo: np.ndarray, nivel_confianca: float = 0.95
) -> dict[str, float]:
    """Estimativa da probabilidade do topo e incerteza estatistica da simulacao."""
    vetor = np.asarray(falhas_topo, dtype=bool)
    if vetor.ndim != 1 or vetor.size == 0:
        raise ValueError("falhas_topo deve ser um array 1D nao vazio")
    return estimar_estatisticas_binomiais(
        n_falhas=int(np.count_nonzero(vetor)),
        n_historias=int(vetor.size),
        nivel_confianca=nivel_confianca,
    )


def rodar_simulacao_base(
    arvore: mod_arvore.ArvoreDeFalhas,
    probabilidades: dict[str, float],
    n_historias: int,
    semente: int,
    tamanho_lote: int = TAMANHO_LOTE_PADRAO,
    nivel_confianca: float = 0.95,
) -> tuple[dict[str, float | int | str], pd.DataFrame]:
    """Executa a simulacao de Monte Carlo em lotes (modelo base: redundancia ativa).

    Returns:
        Tupla ``(resumo, importancias_mc)``:
            - ``resumo``: dicionario com estimativa de P(topo), ICs e metadados;
            - ``importancias_mc``: DataFrame com contagem de participacao de cada
              evento basico nas falhas do topo e aproximacao empirica de
              Fussell-Vesely ``P(E_i | TOPO)``.
    """
    if n_historias <= 0:
        raise ValueError(f"n_historias deve ser positivo, recebido: {n_historias}")
    if tamanho_lote <= 0:
        raise ValueError(f"tamanho_lote deve ser positivo, recebido: {tamanho_lote}")

    eventos = arvore.lista_eventos_basicos()
    gerador = preparar_gerador(semente)

    n_falhas_total = 0
    falhas_por_evento = np.zeros(len(eventos), dtype=np.int64)
    restante = int(n_historias)

    while restante > 0:
        n_lote = min(tamanho_lote, restante)
        estados_lote = sortear_estados(eventos, probabilidades, gerador, n_lote)
        falhas_lote = avaliar_historias(arvore, eventos, estados_lote)

        k_lote = int(np.count_nonzero(falhas_lote))
        if k_lote > 0:
            n_falhas_total += k_lote
            falhas_por_evento += estados_lote[falhas_lote].sum(axis=0, dtype=np.int64)

        restante -= n_lote

    resumo: dict[str, float | int | str] = {
        "modelo": "redundancia_ativa",
        **estimar_estatisticas_binomiais(
            n_falhas=n_falhas_total,
            n_historias=int(n_historias),
            nivel_confianca=nivel_confianca,
        ),
        "semente": int(semente),
    }

    if n_falhas_total > 0:
        fv_mc = falhas_por_evento / n_falhas_total
    else:
        fv_mc = np.full(len(eventos), np.nan, dtype=float)

    importancias = (
        pd.DataFrame(
            {
                "id_evento": eventos,
                "prob_missao": [probabilidades[ev] for ev in eventos],
                "falhas_no_topo": falhas_por_evento,
                "fussell_vesely_mc": fv_mc,
            }
        )
        .sort_values(by=["fussell_vesely_mc", "id_evento"], ascending=[False, True])
        .reset_index(drop=True)
    )

    return resumo, importancias


def tratar_bomba_reserva(
    estados: np.ndarray,
    eventos: list[str],
    tempo_missao_h: float | None = None,
    gerador: np.random.Generator | None = None,
    mttr_h: float | None = None,
    fator_espera: float = 0.0,
    principal_parte_em_t0: bool = False,
    n_equipes_reparo: int = 1,
) -> np.ndarray:
    """Aplica logica de bomba reserva em espera (standby) e reparo opcional.

    Delega para ``monte_carlo.dinamico.aplicar_standby_em_estados`` sem alterar
    ``modelo/arvore_falhas.yaml``. Quando ``mttr_h`` e ``None`` (padrao atual,
    sem dados de MTTR inventados), simula bomba em espera sem reparo.
    """
    from monte_carlo import dinamico as mod_dinamico

    config = mod_dados.carregar_config()
    t_missao = (
        float(tempo_missao_h)
        if tempo_missao_h is not None
        else float(config["tempo_missao_h"])
    )
    rng = (
        gerador
        if gerador is not None
        else preparar_gerador(int(config["semente_aleatoria"]))
    )
    params_mdp = mod_dinamico.carregar_parametros_decompostos()["MDP"]
    return mod_dinamico.aplicar_standby_em_estados(
        estados=estados,
        eventos=eventos,
        parametros_mdp=params_mdp,
        tempo_missao_h=t_missao,
        gerador=rng,
        mttr_h=mttr_h,
        fator_espera=fator_espera,
        principal_parte_em_t0=principal_parte_em_t0,
        n_equipes_reparo=n_equipes_reparo,
    )


def salvar_resultados(resultados: dict, caminho: Path | None = None) -> Path:
    """Salva ``monte_carlo/resultados/mc_resumo.csv``."""
    destino = Path(caminho) if caminho is not None else PASTA_RESULTADOS / "mc_resumo.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([resultados]).to_csv(destino, index=False)
    return destino


def salvar_importancias_mc(
    importancias: pd.DataFrame, caminho: Path | None = None
) -> Path:
    """Salva ``monte_carlo/resultados/mc_importancias.csv``."""
    destino = (
        Path(caminho)
        if caminho is not None
        else PASTA_RESULTADOS / "mc_importancias.csv"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    importancias.to_csv(destino, index=False)
    return destino


def main() -> None:
    """Ponto de entrada: roda a simulacao base completa e salva os resultados."""
    config = mod_dados.carregar_config()
    arvore = mod_arvore.carregar_arvore()
    parametros = mod_dados.carregar_parametros_eventos()

    eventos = arvore.lista_eventos_basicos()
    probabilidades = extrair_probabilidades_missao(parametros, eventos)

    n_simulacoes = int(config["n_simulacoes"])
    semente = int(config["semente_aleatoria"])
    tempo_missao_h = float(config["tempo_missao_h"])

    resumo, importancias = rodar_simulacao_base(
        arvore=arvore,
        probabilidades=probabilidades,
        n_historias=n_simulacoes,
        semente=semente,
    )
    resumo["tempo_missao_h"] = tempo_missao_h

    caminho_resumo = salvar_resultados(resumo)
    caminho_imp = salvar_importancias_mc(importancias)

    print("=" * 70)
    print("Frente 4 - Simulacao de Monte Carlo (Modelo Base: Redundancia Ativa)")
    print("=" * 70)
    print(f"Tempo de missao:        {tempo_missao_h:g} h")
    print(f"Historias simuladas:    {resumo['n_historias']:,}")
    print(f"Semente aleatoria:      {resumo['semente']}")
    print(f"Falhas do evento topo:  {resumo['n_falhas']}")
    print(f"P(TOPO) estimada:       {resumo['p_topo']:.4E}")
    print(f"Erro padrao:            {resumo['erro_padrao']:.4E}")
    if not math.isnan(float(resumo["erro_relativo"])):
        print(f"Erro relativo (SE/p):   {100.0 * float(resumo['erro_relativo']):.2f}%")
    print(
        f"IC 95% (Wilson):        [{resumo['ic_wilson_inf']:.4E}, "
        f"{resumo['ic_wilson_sup']:.4E}]"
    )
    print(
        f"IC 95% (Wald):          [{resumo['ic_wald_inf']:.4E}, "
        f"{resumo['ic_wald_sup']:.4E}]"
    )
    print(
        f"IC 95% (Clopper-P.):    [{resumo['ic_clopper_pearson_inf']:.4E}, "
        f"{resumo['ic_clopper_pearson_sup']:.4E}]"
    )
    print("-" * 70)
    print(f"Resumo salvo em:        {caminho_resumo}")
    print(f"Importancias salvas em: {caminho_imp}")
    print("=" * 70)


if __name__ == "__main__":
    main()

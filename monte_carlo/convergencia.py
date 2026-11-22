"""Frente 4 - Estudo de convergencia da simulacao de Monte Carlo.

O que este arquivo faz:

- Reaproveita o nucleo vetorizado em lotes de ``monte_carlo.simulacao`` para
  acompanhar a estimativa acumulada de P(TOPO) em checkpoints crescentes de
  historias (grade logaritmica).
- Calcula em cada checkpoint: estimativa pontual, erro padrao, erro relativo
  (SE / p), meia-largura relativa do IC 95% e limites de Wald, Wilson e
  Clopper-Pearson.
- Determina o menor numero de historias que estabiliza abaixo de um erro
  relativo alvo (``n_historias_necessario``) e fornece a formula teorica de
  dimensionamento (``n_historias_teorico``) para justificar ``n_simulacoes`` em
  ``config/parametros_globais.yaml``.
- Salva ``mc_convergencia.csv`` e ``mc_convergencia.png`` em
  ``monte_carlo/resultados/``.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

# Permite rodar o script diretamente (ex.: python monte_carlo/convergencia.py).
RAIZ_REPO = Path(__file__).resolve().parent.parent
if str(RAIZ_REPO) not in sys.path:
    sys.path.insert(0, str(RAIZ_REPO))

from ccws import arvore as mod_arvore  # noqa: E402
from ccws import dados as mod_dados  # noqa: E402
from monte_carlo import simulacao as mc  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
CAMINHO_ANALITICO_PADRAO = RAIZ_REPO / "analitico" / "resultados" / "prob_topo.csv"


def gerar_checkpoints(
    n_total: int,
    n_pontos: int = 80,
    n_minimo: int = 1_000,
) -> list[int]:
    """Gera grade crescente de checkpoints em escala logaritmica ate ``n_total``."""
    if n_total <= 0:
        raise ValueError(f"n_total deve ser positivo, recebido: {n_total}")
    if n_pontos <= 0:
        raise ValueError(f"n_pontos deve ser positivo, recebido: {n_pontos}")

    if n_total <= 200:
        return list(range(1, n_total + 1))

    inicio = min(max(1, n_minimo), n_total)
    brutos = np.geomspace(inicio, n_total, num=n_pontos)
    pontos = sorted({int(round(v)) for v in brutos if 1 <= int(round(v)) <= n_total})
    if pontos[-1] != n_total:
        pontos.append(n_total)
    return pontos


def _linha_convergencia(
    n_falhas: int, n_historias: int, nivel_confianca: float
) -> dict[str, float | int]:
    """Monta um registro da curva de convergencia em um checkpoint."""
    est = mc.estimar_estatisticas_binomiais(
        n_falhas=n_falhas,
        n_historias=n_historias,
        nivel_confianca=nivel_confianca,
    )
    p = float(est["p_topo"])
    meia_wilson = 0.5 * (float(est["ic_wilson_sup"]) - float(est["ic_wilson_inf"]))
    meia_rel_ic = (meia_wilson / p) if n_falhas > 0 else float("nan")

    return {
        "n_historias": int(est["n_historias"]),
        "n_falhas": int(est["n_falhas"]),
        "estimativa": p,
        "erro_padrao": float(est["erro_padrao"]),
        "erro_relativo": float(est["erro_relativo"]),
        "meia_largura_rel_ic95": meia_rel_ic,
        "ic95_inf": float(est["ic95_inf"]),
        "ic95_sup": float(est["ic95_sup"]),
        "ic_wald_inf": float(est["ic_wald_inf"]),
        "ic_wald_sup": float(est["ic_wald_sup"]),
        "ic_wilson_inf": float(est["ic_wilson_inf"]),
        "ic_wilson_sup": float(est["ic_wilson_sup"]),
        "ic_clopper_pearson_inf": float(est["ic_clopper_pearson_inf"]),
        "ic_clopper_pearson_sup": float(est["ic_clopper_pearson_sup"]),
    }


def curva_de_convergencia(
    falhas_topo: np.ndarray,
    checkpoints: Sequence[int] | None = None,
    nivel_confianca: float = 0.95,
) -> pd.DataFrame:
    """Estimativa acumulada da probabilidade do topo ao longo das historias.

    Args:
        falhas_topo: array booleano 1D com o resultado de cada historia.
        checkpoints: indices (1-based) de ``n_historias`` a registrar. Se
            omitido, usa todos os pontos para ``N <= 200`` ou uma grade
            logaritmica ate ``N``.
        nivel_confianca: nivel dos intervalos de confianca (padrao: 0.95).

    Returns:
        DataFrame com ``n_historias``, ``n_falhas``, ``estimativa``,
        ``erro_padrao``, ``erro_relativo``, ``meia_largura_rel_ic95`` e limites
        dos ICs (Wilson, Wald e Clopper-Pearson).
    """
    vetor = np.asarray(falhas_topo, dtype=bool)
    if vetor.ndim != 1 or vetor.size == 0:
        raise ValueError("falhas_topo deve ser um array 1D nao vazio")

    n_total = int(vetor.size)
    if checkpoints is None:
        pontos = gerar_checkpoints(n_total)
    else:
        pontos = sorted({int(p) for p in checkpoints})
        if not pontos or pontos[0] < 1 or pontos[-1] > n_total:
            raise ValueError(
                f"checkpoints devem estar no intervalo [1, {n_total}], recebido: {pontos}"
            )

    acumulado = np.cumsum(vetor, dtype=np.int64)
    linhas = [
        _linha_convergencia(
            n_falhas=int(acumulado[n - 1]),
            n_historias=n,
            nivel_confianca=nivel_confianca,
        )
        for n in pontos
    ]
    return pd.DataFrame(linhas)


def rodar_estudo_convergencia(
    arvore: mod_arvore.ArvoreDeFalhas,
    probabilidades: dict[str, float],
    n_historias: int,
    semente: int,
    checkpoints: Sequence[int] | None = None,
    tamanho_lote: int = mc.TAMANHO_LOTE_PADRAO,
    nivel_confianca: float = 0.95,
) -> pd.DataFrame:
    """Gera a curva de convergencia processando em lotes (memoria limitada).

    Usa exatamente a mesma divisao de lotes e a mesma semente de
    ``simulacao.rodar_simulacao_base``, garantindo que o ponto final da curva
    bata exatamente com ``mc_resumo.csv``.
    """
    if n_historias <= 0:
        raise ValueError(f"n_historias deve ser positivo, recebido: {n_historias}")
    if tamanho_lote <= 0:
        raise ValueError(f"tamanho_lote deve ser positivo, recebido: {tamanho_lote}")

    pontos = (
        gerar_checkpoints(n_historias)
        if checkpoints is None
        else sorted({int(p) for p in checkpoints})
    )
    if not pontos or pontos[0] < 1 or pontos[-1] > n_historias:
        raise ValueError(
            f"checkpoints devem estar no intervalo [1, {n_historias}], recebido: {pontos}"
        )

    eventos = arvore.lista_eventos_basicos()
    gerador = mc.preparar_gerador(semente)

    linhas: list[dict[str, float | int]] = []
    idx_cp = 0
    processadas = 0
    falhas_acum = 0

    while processadas < n_historias:
        n_lote = min(tamanho_lote, n_historias - processadas)
        estados_lote = mc.sortear_estados(eventos, probabilidades, gerador, n_lote)
        falhas_lote = mc.avaliar_historias(arvore, eventos, estados_lote)

        fim_lote = processadas + n_lote
        # So calcula cumsum do lote se houver checkpoints caindo dentro dele.
        if idx_cp < len(pontos) and pontos[idx_cp] <= fim_lote:
            cumsum_lote = np.cumsum(falhas_lote, dtype=np.int64)
            while idx_cp < len(pontos) and pontos[idx_cp] <= fim_lote:
                n_cp = pontos[idx_cp]
                k_cp = falhas_acum + int(cumsum_lote[n_cp - processadas - 1])
                linhas.append(_linha_convergencia(k_cp, n_cp, nivel_confianca))
                idx_cp += 1
            falhas_acum += int(cumsum_lote[-1])
        else:
            falhas_acum += int(np.count_nonzero(falhas_lote))

        processadas = fim_lote

    return pd.DataFrame(linhas)


def n_historias_necessario(
    curva: pd.DataFrame,
    erro_relativo_alvo: float,
    coluna_erro: str = "erro_relativo",
) -> int | None:
    """Menor ``n_historias`` a partir do qual o erro permanece ``<= erro_relativo_alvo``.

    Exige estabilidade ate o final da curva (todos os pontos a partir do indice
    encontrado precisam ser finitos e ``<= erro_relativo_alvo``), evitando
    falsos positivos em oscilacoes iniciais. Retorna ``None`` se o alvo nao for
    atingido no horizonte simulado.
    """
    if not (0.0 < erro_relativo_alvo < 1.0):
        raise ValueError(
            f"erro_relativo_alvo deve estar em (0, 1), recebido: {erro_relativo_alvo}"
        )
    if curva.empty:
        return None
    if coluna_erro not in curva.columns or "n_historias" not in curva.columns:
        raise KeyError(
            f"curva deve conter as colunas 'n_historias' e '{coluna_erro}'"
        )

    ordenada = curva.sort_values("n_historias").reset_index(drop=True)
    erros = ordenada[coluna_erro].to_numpy(dtype=float)
    satisfaz = np.isfinite(erros) & (erros <= erro_relativo_alvo)

    # Encontra o menor indice i tal que satisfaz[i:] e todo True.
    if not satisfaz[-1]:
        return None

    for i in range(len(satisfaz) - 1, -1, -1):
        if not satisfaz[i]:
            return int(ordenada.loc[i + 1, "n_historias"])
    return int(ordenada.loc[0, "n_historias"])


def n_historias_teorico(
    p_estimado: float,
    erro_relativo_alvo: float,
    criterio: str = "erro_padrao",
    nivel_confianca: float = 0.95,
) -> int:
    """Formula analitica de dimensionamento de historias para eventos binomiais.

    - ``criterio="erro_padrao"``: ``SE / p <= erro_relativo_alvo`` ->
      ``N >= (1 - p) / (p * eps^2)``.
    - ``criterio="ic"``: meia-largura relativa do IC <= ``erro_relativo_alvo`` ->
      ``N >= z^2 * (1 - p) / (p * eps^2)``.
    """
    if not (0.0 < p_estimado < 1.0):
        raise ValueError(f"p_estimado deve estar em (0, 1), recebido: {p_estimado}")
    if not (0.0 < erro_relativo_alvo < 1.0):
        raise ValueError(
            f"erro_relativo_alvo deve estar em (0, 1), recebido: {erro_relativo_alvo}"
        )
    if criterio not in {"erro_padrao", "ic"}:
        raise ValueError(f"criterio invalido: {criterio!r} (use 'erro_padrao' ou 'ic')")

    fator = 1.0
    if criterio == "ic":
        z = float(stats.norm.ppf(1.0 - (1.0 - nivel_confianca) / 2.0))
        fator = z * z

    return int(math.ceil(fator * (1.0 - p_estimado) / (p_estimado * erro_relativo_alvo**2)))


def carregar_referencia_analitica(caminho: Path | None = None) -> float | None:
    """Le P(TOPO) analitica de ``analitico/resultados/prob_topo.csv`` se existir."""
    arq = Path(caminho) if caminho is not None else CAMINHO_ANALITICO_PADRAO
    if not arq.is_file():
        return None

    df = pd.read_csv(arq)
    if df.empty:
        return None
    for coluna in ("p_topo", "prob_topo", "probabilidade_topo", "inclusao_exclusao", "evento_raro"):
        if coluna in df.columns and pd.notna(df[coluna].iloc[0]):
            return float(df[coluna].iloc[0])
    return None


def salvar_curva(curva: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva ``monte_carlo/resultados/mc_convergencia.csv``."""
    destino = (
        Path(caminho)
        if caminho is not None
        else PASTA_RESULTADOS / "mc_convergencia.csv"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    curva.to_csv(destino, index=False)
    return destino


def grafico_convergencia(
    curva: pd.DataFrame,
    caminho: Path | None = None,
    p_analitico: float | None = None,
    erro_relativo_alvo: float = 0.10,
) -> Path:
    """Salva o grafico de convergencia (estimativa + IC 95% e erro relativo) em PNG."""
    if curva.empty:
        raise ValueError("curva de convergencia esta vazia")

    destino = (
        Path(caminho)
        if caminho is not None
        else PASTA_RESULTADOS / "mc_convergencia.png"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = curva.sort_values("n_historias").reset_index(drop=True)
    n_vals = df["n_historias"].to_numpy(dtype=float)
    est = df["estimativa"].to_numpy(dtype=float)
    ic_inf = df["ic95_inf"].to_numpy(dtype=float)
    ic_sup = df["ic95_sup"].to_numpy(dtype=float)
    erro_rel_pct = 100.0 * df["erro_relativo"].to_numpy(dtype=float)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9.5, 7.2), sharex=True, gridspec_kw={"height_ratios": [1.3, 1.0]}
    )

    # ---- Painel 1: Estimativa acumulada de P(TOPO) e faixa do IC 95% (Wilson)
    ax1.fill_between(
        n_vals,
        ic_inf,
        ic_sup,
        color="#4C78A8",
        alpha=0.22,
        label="IC 95% (Wilson)",
    )
    ax1.plot(
        n_vals,
        est,
        color="#1F4E79",
        linewidth=1.8,
        label=r"Estimativa $\hat{P}(\mathrm{TOPO})$",
    )
    if p_analitico is not None:
        ax1.axhline(
            p_analitico,
            color="#D62728",
            linestyle="--",
            linewidth=1.4,
            label=f"Referencia analitica ({p_analitico:.2E})",
        )

    p_final = float(est[-1])
    k_final = int(df["n_falhas"].iloc[-1])
    n_final = int(df["n_historias"].iloc[-1])
    ax1.set_xscale("log")
    ax1.set_ylabel(r"$P(\mathrm{TOPO})$")
    ax1.set_title(
        f"Convergencia da Simulacao de Monte Carlo — CCWS "
        f"(N = {n_final:,}, falhas = {k_final}, P = {p_final:.2E})"
    )
    ax1.grid(True, which="both", linestyle=":", alpha=0.55)
    ax1.legend(loc="upper right", frameon=True)

    # Limite superior limpo (ultima decada) para destacar a convergencia final
    if p_final > 0:
        mascara_final = n_vals >= n_final / 10.0
        ymax_ref = (
            float(np.nanmax(ic_sup[mascara_final]))
            if np.any(mascara_final)
            else float(np.nanmax(ic_sup))
        )
        ymax = max(ymax_ref, p_final * 3.0)
        if p_analitico is not None:
            ymax = max(ymax, p_analitico * 2.0)
        ax1.set_ylim(0.0, ymax * 1.15)
    ax1.ticklabel_format(axis="y", style="sci", scilimits=(-2, 3))

    # ---- Painel 2: Erro relativo (SE / p) vs. curva teorica O(N^-1/2)
    validos = np.isfinite(erro_rel_pct) & (erro_rel_pct > 0)
    if np.any(validos):
        ax2.plot(
            n_vals[validos],
            erro_rel_pct[validos],
            color="#2E7D32",
            linewidth=1.8,
            marker="o",
            markersize=3,
            label=r"Erro relativo observado ($\mathrm{SE}/\hat{p}$)",
        )
    if p_final > 0:
        teorico_pct = 100.0 * np.sqrt((1.0 - p_final) / (p_final * n_vals))
        ax2.plot(
            n_vals,
            teorico_pct,
            color="#555555",
            linestyle="--",
            linewidth=1.3,
            label=r"Tendencia teorica $\propto N^{-1/2}$",
        )

    ax2.axhline(
        100.0 * erro_relativo_alvo,
        color="#E65100",
        linestyle=":",
        linewidth=1.4,
        label=f"Meta de erro relativo ({100.0 * erro_relativo_alvo:.0f}%)",
    )
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Numero de historias simuladas (N)")
    ax2.set_ylabel("Erro relativo (%)")
    ax2.grid(True, which="both", linestyle=":", alpha=0.55)
    ax2.legend(loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(destino, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return destino


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estudo de convergencia da simulacao de Monte Carlo do CCWS."
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=None,
        help=(
            "Numero maximo de historias (opcional; se omitido, usa n_simulacoes "
            "de config/parametros_globais.yaml)."
        ),
    )
    parser.add_argument(
        "--erro-alvo",
        type=float,
        default=0.10,
        help="Erro relativo alvo (SE/p) destacado no grafico e relatorio (padrao: 0.10).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Ponto de entrada: gera a curva, o grafico e o dimensionamento de N."""
    args = _parse_args(argv)

    config = mod_dados.carregar_config()
    arvore = mod_arvore.carregar_arvore()
    parametros = mod_dados.carregar_parametros_eventos()
    probabilidades = mc.extrair_probabilidades_missao(
        parametros, arvore.lista_eventos_basicos()
    )

    n_max = int(args.n_max) if args.n_max is not None else int(config["n_simulacoes"])
    semente = int(config["semente_aleatoria"])
    p_analitico = carregar_referencia_analitica()

    curva = rodar_estudo_convergencia(
        arvore=arvore,
        probabilidades=probabilidades,
        n_historias=n_max,
        semente=semente,
    )

    caminho_csv = salvar_curva(curva)
    caminho_png = grafico_convergencia(
        curva,
        p_analitico=p_analitico,
        erro_relativo_alvo=args.erro_alvo,
    )

    ultimo = curva.iloc[-1]
    p_final = float(ultimo["estimativa"])
    n_obs_10 = n_historias_necessario(curva, 0.10)
    n_obs_05 = n_historias_necessario(curva, 0.05)

    print("=" * 72)
    print("Frente 4 - Estudo de Convergencia da Simulacao de Monte Carlo")
    print("=" * 72)
    print(f"Historias simuladas:    {int(ultimo['n_historias']):,} (semente {semente})")
    print(f"Falhas do topo:         {int(ultimo['n_falhas'])}")
    print(f"P(TOPO) final:          {p_final:.4E}")
    if not math.isnan(float(ultimo["erro_relativo"])):
        print(f"Erro relativo (SE/p):   {100.0 * float(ultimo['erro_relativo']):.2f}%")
        print(
            f"Meia-larg. rel. IC 95%: {100.0 * float(ultimo['meia_largura_rel_ic95']):.2f}%"
        )
    print(
        f"IC 95% (Wilson):        [{float(ultimo['ic_wilson_inf']):.4E}, "
        f"{float(ultimo['ic_wilson_sup']):.4E}]"
    )
    print("-" * 72)
    print("Dimensionamento de N (a partir da curva e da formula binomial):")
    print(
        f"  Observado (SE/p <= 10%): "
        f"{f'{n_obs_10:,}' if n_obs_10 is not None else 'nao atingido no horizonte'}"
    )
    print(
        f"  Observado (SE/p <=  5%): "
        f"{f'{n_obs_05:,}' if n_obs_05 is not None else 'nao atingido no horizonte'}"
    )
    if p_final > 0:
        print(
            f"  Teorico (SE/p <= 10%):       {n_historias_teorico(p_final, 0.10, 'erro_padrao'):,}"
        )
        print(
            f"  Teorico (SE/p <=  5%):       {n_historias_teorico(p_final, 0.05, 'erro_padrao'):,}"
        )
        print(
            f"  Teorico (IC 95% <= +-10%):   {n_historias_teorico(p_final, 0.10, 'ic'):,}"
        )
        print(
            f"  Teorico (IC 95% <= +- 5%):   {n_historias_teorico(p_final, 0.05, 'ic'):,}"
        )
    print("-" * 72)
    print(f"Curva salva em:         {caminho_csv}")
    print(f"Grafico salvo em:       {caminho_png}")
    print("=" * 72)


if __name__ == "__main__":
    main()

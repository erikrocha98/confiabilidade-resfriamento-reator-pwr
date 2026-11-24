"""Frente 3 - Medidas de importancia dos eventos basicos do CCWS.

O que este arquivo deve fazer, para cada evento basico:

- Fussell-Vesely (contribuicao fracional do evento para a probabilidade do topo).
- Birnbaum (derivada da probabilidade do topo em relacao a probabilidade do evento).
- RAW - Risk Achievement Worth (evento com probabilidade 1).
- RRW - Risk Reduction Worth (evento com probabilidade 0).

Entradas: cortes minimos (``cortes_minimos.py``) e probabilidades por evento
(``probabilidade_topo.py``). Saidas: ranking dos eventos em
``analitico/resultados/``, que a frente 5 usa para escolher os cenarios de
sensibilidade.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ccws import arvore as mod_arvore
from ccws import dados as mod_dados
from analitico.cortes_minimos import carregar_cortes, obter_cortes_minimos
from analitico.probabilidade_topo import (
    probabilidade_topo_inclusao_exclusao,
    probabilidades_de_missao,
)

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def _probabilidade_condicional(
    cortes: list[frozenset[str]],
    probabilidades: dict[str, float],
    evento: str,
    valor: float,
) -> float:
    condicionais = dict(probabilidades)
    condicionais[evento] = valor
    return probabilidade_topo_inclusao_exclusao(cortes, condicionais)


def fussell_vesely(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Importancia de Fussell-Vesely de cada evento basico."""
    topo = probabilidade_topo_inclusao_exclusao(cortes, probabilidades)
    if topo == 0.0:
        return {evento: 0.0 for evento in probabilidades}
    return {
        evento: (
            topo - _probabilidade_condicional(cortes, probabilidades, evento, 0.0)
        )
        / topo
        for evento in probabilidades
    }


def birnbaum(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Importancia de Birnbaum de cada evento basico."""
    return {
        evento: _probabilidade_condicional(cortes, probabilidades, evento, 1.0)
        - _probabilidade_condicional(cortes, probabilidades, evento, 0.0)
        for evento in probabilidades
    }


def raw(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Risk Achievement Worth de cada evento basico."""
    topo = probabilidade_topo_inclusao_exclusao(cortes, probabilidades)
    return {
        evento: _probabilidade_condicional(cortes, probabilidades, evento, 1.0) / topo
        if topo
        else float("inf")
        for evento in probabilidades
    }


def rrw(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Risk Reduction Worth de cada evento basico."""
    topo = probabilidade_topo_inclusao_exclusao(cortes, probabilidades)
    resultado = {}
    for evento in probabilidades:
        reduzida = _probabilidade_condicional(cortes, probabilidades, evento, 0.0)
        resultado[evento] = topo / reduzida if reduzida else float("inf")
    return resultado


def tabela_importancias(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> pd.DataFrame:
    """Reune as quatro medidas em uma tabela ordenada por Fussell-Vesely."""
    medidas = {
        "fussell_vesely": fussell_vesely(cortes, probabilidades),
        "birnbaum": birnbaum(cortes, probabilidades),
        "raw": raw(cortes, probabilidades),
        "rrw": rrw(cortes, probabilidades),
    }
    linhas = []
    for evento in probabilidades:
        linhas.append(
            {
                "id_evento": evento,
                "prob_missao": probabilidades[evento],
                **{nome: valores[evento] for nome, valores in medidas.items()},
            }
        )
    tabela = pd.DataFrame(linhas).sort_values(
        ["fussell_vesely", "birnbaum", "id_evento"],
        ascending=[False, False, True],
    )
    tabela.insert(0, "ranking_fv", range(1, len(tabela) + 1))
    return tabela.reset_index(drop=True)


def salvar_importancias(tabela: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva ``analitico/resultados/importancias.csv``."""
    caminho = caminho or PASTA_RESULTADOS / "importancias.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(caminho, index=False)

    top = tabela.head(12).sort_values("fussell_vesely")
    fig, eixo = plt.subplots(figsize=(9, 5.5))
    eixo.barh(top["id_evento"], top["fussell_vesely"], color="#1f6f8b")
    eixo.set_xlabel("Importancia de Fussell-Vesely")
    eixo.set_ylabel("Evento basico")
    eixo.set_title("CCWS - ranking dos eventos basicos (missao de 24 h)")
    eixo.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(caminho.parent / "ranking_fussell_vesely.png", dpi=200)
    plt.close(fig)
    return caminho


def main() -> None:
    """Ponto de entrada: calcula e salva as medidas de importancia."""
    arvore = mod_arvore.carregar_arvore()
    config = mod_dados.carregar_config()
    parametros = mod_dados.carregar_parametros_eventos()
    probabilidades = probabilidades_de_missao(parametros, float(config["tempo_missao_h"]))
    caminho_cortes = PASTA_RESULTADOS / "cortes_minimos.csv"
    cortes = carregar_cortes(caminho_cortes) if caminho_cortes.exists() else obter_cortes_minimos(arvore)
    tabela = tabela_importancias(cortes, probabilidades)
    caminho = salvar_importancias(tabela)
    print(tabela.head(10).to_string(index=False))
    print(f"salvo em: {caminho}")


if __name__ == "__main__":
    main()

"""Frente 5 - Comparacao entre a solucao analitica e a simulacao de Monte Carlo.

O que este arquivo deve fazer:

- Ler as saidas da frente 3 (``analitico/resultados/``) e da frente 4
  (``monte_carlo/resultados/``).
- Comparar a probabilidade do evento topo pelos dois metodos: diferenca
  absoluta, diferenca relativa e verificacao de se o valor analitico cai dentro
  do intervalo de confianca da simulacao.
- Comparar tambem os rankings de importancia, se a frente 4 produzir estimativas
  de importancia por simulacao.
- Gerar a tabela e as figuras de comparacao para o relatorio final, em
  ``sensibilidade/resultados/``.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ_REPO = Path(__file__).resolve().parent.parent
PASTA_ANALITICO = RAIZ_REPO / "analitico" / "resultados"
PASTA_MONTE_CARLO = RAIZ_REPO / "monte_carlo" / "resultados"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def carregar_resultado_analitico(pasta: Path | None = None) -> dict:
    """Le a probabilidade do topo calculada pela frente 3."""
    # TODO: ler analitico/resultados/prob_topo.csv; erro claro se nao existir
    # (a frente 3 precisa ter rodado antes).
    raise NotImplementedError


def carregar_resultado_monte_carlo(pasta: Path | None = None) -> dict:
    """Le a estimativa da probabilidade do topo produzida pela frente 4."""
    # TODO: ler monte_carlo/resultados/mc_resumo.csv.
    raise NotImplementedError


def comparar_probabilidade_topo(analitico: dict, monte_carlo: dict) -> pd.DataFrame:
    """Compara P(topo) analitica x Monte Carlo (diferenca absoluta, relativa, IC)."""
    raise NotImplementedError


def comparar_importancias(
    importancias_analiticas: pd.DataFrame, importancias_mc: pd.DataFrame
) -> pd.DataFrame:
    """Compara os rankings de importancia dos dois metodos, se houver ambos."""
    raise NotImplementedError


def figuras_comparacao(comparacao: pd.DataFrame, pasta: Path | None = None) -> list[Path]:
    """Gera as figuras de comparacao para o relatorio."""
    # TODO: matplotlib; salvar em sensibilidade/resultados/.
    raise NotImplementedError


def main() -> None:
    """Ponto de entrada: monta a comparacao e salva tabela e figuras."""
    raise NotImplementedError


if __name__ == "__main__":
    main()

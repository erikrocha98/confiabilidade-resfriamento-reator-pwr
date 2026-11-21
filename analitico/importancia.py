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

from pathlib import Path

import pandas as pd

from ccws import arvore as mod_arvore  # noqa: F401  (usado quando implementado)
from ccws import dados as mod_dados  # noqa: F401

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def fussell_vesely(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Importancia de Fussell-Vesely de cada evento basico."""
    # TODO: somar as probabilidades dos cortes que contem o evento / prob do topo.
    raise NotImplementedError


def birnbaum(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Importancia de Birnbaum de cada evento basico."""
    # TODO: P(topo | evento falhou) - P(topo | evento nao falhou).
    raise NotImplementedError


def raw(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Risk Achievement Worth de cada evento basico."""
    # TODO: P(topo | p_evento = 1) / P(topo).
    raise NotImplementedError


def rrw(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> dict[str, float]:
    """Risk Reduction Worth de cada evento basico."""
    # TODO: P(topo) / P(topo | p_evento = 0).
    raise NotImplementedError


def tabela_importancias(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> pd.DataFrame:
    """Reune as quatro medidas em uma tabela ordenada por Fussell-Vesely."""
    # TODO: montar DataFrame com colunas id_evento, fussell_vesely, birnbaum, raw, rrw.
    raise NotImplementedError


def salvar_importancias(tabela: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva ``analitico/resultados/importancias.csv``."""
    # TODO: salvar em CSV e, se o grupo quiser, um grafico de barras do ranking.
    raise NotImplementedError


def main() -> None:
    """Ponto de entrada: calcula e salva as medidas de importancia."""
    raise NotImplementedError


if __name__ == "__main__":
    main()

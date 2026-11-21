"""Frente 4 - Estudo de convergencia da simulacao de Monte Carlo.

O que este arquivo deve fazer:

- Rodar a simulacao (ou reaproveitar as historias de ``simulacao.py``) para
  numeros crescentes de historias.
- Acompanhar a estimativa da probabilidade do topo e a largura do intervalo de
  confianca em funcao do numero de historias.
- Indicar quantas historias sao suficientes para a precisao que o grupo quer
  (justificar o ``n_simulacoes`` de ``config/parametros_globais.yaml``).
- Gerar o grafico de convergencia para o relatorio, salvo em
  ``monte_carlo/resultados/``.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np  # noqa: F401  (usado quando implementado)
import pandas as pd

from ccws import dados as mod_dados  # noqa: F401

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def curva_de_convergencia(falhas_topo: "np.ndarray") -> pd.DataFrame:
    """Estimativa acumulada da probabilidade do topo historia a historia.

    Returns:
        Tabela com ``n_historias``, ``estimativa``, ``erro_padrao``, limites do IC.
    """
    # TODO: media acumulada das falhas do topo e erro padrao correspondente.
    raise NotImplementedError


def n_historias_necessario(curva: pd.DataFrame, erro_relativo_alvo: float) -> int:
    """Menor numero de historias que atinge o erro relativo alvo."""
    # TODO: varrer a curva e devolver o primeiro n que satisfaz o criterio.
    raise NotImplementedError


def grafico_convergencia(curva: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva o grafico de convergencia em ``monte_carlo/resultados/``."""
    # TODO: matplotlib: estimativa x n_historias com faixa do IC e linha do valor analitico.
    raise NotImplementedError


def main() -> None:
    """Ponto de entrada: gera a curva, o grafico e o n recomendado."""
    raise NotImplementedError


if __name__ == "__main__":
    main()

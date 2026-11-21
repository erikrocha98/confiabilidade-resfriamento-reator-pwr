"""Frente 3 - Probabilidade de ocorrencia do evento topo do CCWS.

O que este arquivo deve fazer:

- Ler ``config/parametros_globais.yaml`` (tempo de missao) e
  ``dados/parametros_eventos.csv`` via ``ccws.dados``.
- Converter o parametro de cada evento basico em probabilidade de falha no tempo
  de missao (``prob_missao``):
    - ``tipo = demanda``: a probabilidade e a propria media do INL;
    - ``tipo = taxa``: usar o modelo exponencial, 1 - exp(-lambda * t).
- Calcular a probabilidade do evento topo a partir dos cortes minimos
  (aproximacao de evento raro e/ou limite superior / inclusao-exclusao).
- Salvar os resultados em ``analitico/resultados/``.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ccws import arvore as mod_arvore
from ccws import dados as mod_dados

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def probabilidades_de_missao(
    parametros: pd.DataFrame, tempo_missao_h: float
) -> dict[str, float]:
    """Probabilidade de falha de cada evento basico no tempo de missao.

    Args:
        parametros: tabela de ``ccws.dados.carregar_parametros_eventos``.
        tempo_missao_h: tempo de missao em horas (da configuracao global).

    Returns:
        ``{id_evento: probabilidade}``.
    """
    # TODO: tratar tipo = demanda e tipo = taxa; falhar de forma clara se a
    # tabela de dados ainda estiver vazia (frente 2 em andamento).
    raise NotImplementedError


def probabilidade_topo_evento_raro(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> float:
    """Aproximacao de evento raro: soma das probabilidades dos cortes minimos."""
    # TODO: somar o produto das probabilidades dos eventos de cada corte.
    raise NotImplementedError


def probabilidade_topo_inclusao_exclusao(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> float:
    """Probabilidade do topo por inclusao-exclusao (ou limite superior)."""
    # TODO: decidir com o grupo entre inclusao-exclusao completa e min-cut upper bound.
    raise NotImplementedError


def salvar_resultados(resultados: dict, caminho: Path | None = None) -> Path:
    """Salva a probabilidade do topo e as probabilidades por evento em ``resultados/``."""
    # TODO: salvar prob_topo.csv (ou .json) e prob_eventos.csv.
    raise NotImplementedError


def main() -> None:
    """Ponto de entrada: calcula a probabilidade do topo e salva os resultados."""
    # TODO: carregar config, dados, arvore e cortes minimos; calcular e salvar.
    raise NotImplementedError


if __name__ == "__main__":
    main()

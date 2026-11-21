"""Frente 5 - Execucao dos cenarios de analise de sensibilidade.

O que este arquivo deve fazer:

- Ler ``sensibilidade/cenarios.yaml``.
- Para cada cenario, montar os parametros alterados a partir do caso base
  (fator multiplicativo sobre o parametro do evento ou do componente, mudanca de
  tempo de missao, ou indisponibilidade de um trem).
- Recalcular a probabilidade do evento topo pela via analitica (frente 3) e,
  quando fizer sentido, pela simulacao (frente 4).
- Salvar a tabela de resultados por cenario em ``sensibilidade/resultados/``.

Os cenarios NAO contem valores absolutos de taxa ou probabilidade: eles
modificam o caso base por fatores, de modo que nenhum dado e inventado aqui.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml  # noqa: F401  (usado quando implementado)

from ccws import arvore as mod_arvore  # noqa: F401
from ccws import dados as mod_dados  # noqa: F401

PASTA_CENARIOS = Path(__file__).resolve().parent / "cenarios.yaml"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def carregar_cenarios(caminho: Path | None = None) -> list[dict]:
    """Le ``cenarios.yaml`` e devolve a lista de cenarios."""
    # TODO: ler o YAML e validar os campos obrigatorios (id, tipo, alvo).
    raise NotImplementedError


def aplicar_cenario(parametros: pd.DataFrame, cenario: dict) -> pd.DataFrame:
    """Devolve uma copia dos parametros com o cenario aplicado.

    Nao altera a tabela original nem os arquivos em ``dados/``.
    """
    # TODO: tratar tipo = fator_evento, fator_componente, tempo_missao, indisponibilidade.
    raise NotImplementedError


def rodar_cenario(cenario: dict) -> dict:
    """Roda um cenario e devolve as metricas (P(topo) analitica e/ou Monte Carlo)."""
    # TODO: reutilizar as funcoes da frente 3 (e da frente 4, se o grupo decidir).
    raise NotImplementedError


def tabela_resultados(resultados: list[dict]) -> pd.DataFrame:
    """Reune os cenarios em uma tabela comparavel com o caso base."""
    # TODO: colunas id_cenario, p_topo, razao_em_relacao_ao_caso_base, metodo.
    raise NotImplementedError


def salvar_resultados(tabela: pd.DataFrame, caminho: Path | None = None) -> Path:
    """Salva ``sensibilidade/resultados/sensibilidade_cenarios.csv``."""
    raise NotImplementedError


def main() -> None:
    """Ponto de entrada: roda todos os cenarios e salva a tabela comparativa."""
    raise NotImplementedError


if __name__ == "__main__":
    main()

"""Pacote compartilhado do estudo de confiabilidade do CCWS.

Usado pelas frentes 3 (analitico), 4 (Monte Carlo) e 5 (sensibilidade).
Contem apenas o que e comum a todas elas:

- ``ccws.arvore``: leitura e avaliacao da arvore de falhas (frente 1).
- ``ccws.dados``:  leitura e validacao das tabelas de parametros (frente 2)
  e da configuracao global.

Nenhuma analise deve ser implementada aqui.
"""

from ccws import arvore, dados  # noqa: F401  (reexportado por conveniencia)

__all__ = ["arvore", "dados"]

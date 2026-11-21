# Frente 5 - Sensibilidade e integracao

Responsavel: [nome]

Fecha o estudo: roda cenarios de sensibilidade sobre o caso base e compara a
solucao analitica (frente 3) com a simulacao de Monte Carlo (frente 4).

## Entradas

- `analitico/resultados/` (frente 3): `prob_topo.csv`, `importancias.csv`, `cortes_minimos.csv`.
- `monte_carlo/resultados/` (frente 4): `mc_resumo.csv`, `mc_convergencia.csv`.
- `sensibilidade/cenarios.yaml` - definicao dos cenarios (desta frente).
- Indiretamente, `dados/` e `config/` para recalcular os cenarios.

## Saidas esperadas (em `resultados/`)

| Arquivo | Conteudo |
| --- | --- |
| `sensibilidade_cenarios.csv` | Por cenario: P(topo), razao em relacao ao caso base, metodo usado. |
| `comparacao_metodos.csv` | P(topo) analitica x Monte Carlo: diferenca absoluta, relativa, e se o analitico cai no IC 95% da simulacao. |
| `comparacao_metodos.png` | Figura da comparacao para o relatorio. |
| `tornado_sensibilidade.png` | Grafico de sensibilidade (tornado) dos cenarios, se o grupo optar por ele. |

Os arquivos de `resultados/` nao sao versionados; a pasta fica no repo via `.gitkeep`.

## Depende de

Frentes 3 e 4 - precisa das **saidas** delas, nao so do codigo. Ou seja, esta
frente roda por ultimo: `analitico/` e `monte_carlo/` tem que ter sido
executados antes.

## Arquivos

- `cenarios.yaml` - definicao dos cenarios (fatores sobre o caso base, tempo de missao, indisponibilidade de trem).
- `rodar_cenarios.py` - aplica cada cenario e recalcula P(topo).
- `comparacao.py` - compara analitico x Monte Carlo (P(topo) e rankings de importancia).

## Regras dos cenarios

- Cenario altera o caso base por **fator multiplicativo** ou por tempo de missao;
  nunca por um valor de taxa escrito a mao. Isso mantem a rastreabilidade dos dados do INL.
- Nenhum script desta frente escreve em `dados/`: os cenarios trabalham sobre
  copias em memoria dos parametros.
- Se a frente 4 adotar logica de bomba reserva (spare), a comparacao
  analitico x Monte Carlo deixa de ser exata. Isso tem que ser dito
  explicitamente na tabela de comparacao e no relatorio.

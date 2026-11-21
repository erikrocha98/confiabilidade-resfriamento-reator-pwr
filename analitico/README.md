# Frente 3 - Solucao analitica

Responsavel: [nome]

Solucao exata (analitica) da arvore de falhas: cortes minimos, probabilidade do
evento topo no tempo de missao e medidas de importancia dos eventos basicos.

## Entradas

- `modelo/arvore_falhas.yaml` (frente 1), lido via `ccws.arvore`.
- `dados/parametros_eventos.csv` e `dados/fatores_alfa_ccf.csv` (frente 2), lidos via `ccws.dados`.
- `config/parametros_globais.yaml` - `tempo_missao_h`.

## Saidas esperadas (em `resultados/`)

| Arquivo | Conteudo |
| --- | --- |
| `cortes_minimos.csv` | Um corte por linha: ordem do corte e eventos basicos. |
| `prob_eventos.csv` | `id_evento`, `prob_missao` usada no calculo e como foi obtida (demanda ou taxa x tempo de missao). |
| `prob_topo.csv` | Probabilidade do evento topo pelas aproximacoes usadas (evento raro, inclusao-exclusao / limite superior). |
| `importancias.csv` | Por evento: Fussell-Vesely, Birnbaum, RAW e RRW, ordenado pelo ranking escolhido. |

Os arquivos de `resultados/` nao sao versionados (ver `.gitignore`); so a pasta
fica no repo, via `.gitkeep`. Quem precisar dos numeros roda os scripts.

## Depende de

Frentes 1 (modelo) e 2 (dados). Enquanto a frente 2 nao terminar a extracao, os
scripts podem ser desenvolvidos e testados com a arvore, mas nao produzem
numeros finais - `python scripts/validar_dados.py` mostra o que falta.

## Arquivos

- `cortes_minimos.py` - obtem e reduz os cortes minimos; confere contra `ccws.arvore.avalia`.
- `probabilidade_topo.py` - converte parametros em probabilidade de missao e calcula P(topo).
- `importancia.py` - Fussell-Vesely, Birnbaum, RAW e RRW.

Ordem de execucao: `cortes_minimos.py` -> `probabilidade_topo.py` -> `importancia.py`.

## Decisoes a registrar no relatorio

- Qual aproximacao foi usada para P(topo) e por que (evento raro x inclusao-exclusao).
- Como as falhas de causa comum (fatores alfa) entraram no modelo, se entraram.
- Convencao de tempo de missao e de unidades das taxas (`1/h`).

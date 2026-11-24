# Frente 3 - Solucao analitica

Responsavel: [preencher]

Solucao exata (analitica) da arvore de falhas: cortes minimos, probabilidade do
evento topo no tempo de missao e medidas de importancia dos eventos basicos.

**Estado:** implementada e validada para a missao de 24 h configurada no
repositorio. Consulte `RESULTADOS.md` para o texto-base do relatorio e
`ROTEIRO_APRESENTACAO.md` para os slides da frente.

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

Ordem de execucao:

```bash
python analitico/cortes_minimos.py
python analitico/probabilidade_topo.py
python analitico/importancia.py
```

Os scripts geram os quatro CSVs previstos e
`resultados/ranking_fussell_vesely.png`.

## Decisoes a registrar no relatorio

- Qual aproximacao foi usada para P(topo) e por que (evento raro x inclusao-exclusao).
- Como as falhas de causa comum (fatores alfa) entraram no modelo, se entraram.
- Convencao de tempo de missao e de unidades das taxas (`1/h`).

## Limitacoes atuais

- O resultado quantitativo vale para 24 h. Os valores de `prob_missao` foram
  agregados nesse horizonte pela frente 2; para 1, 5, 10, 20 ou 40 anos e
  necessario recalcular cada modo de falha a partir de `dados/extracao_bruta.csv`.
- Os fatores alfa de bombas foram extraidos, mas a arvore nao contem eventos
  basicos de causa comum. Assim, o resultado-base assume independencia entre
  os 24 eventos. Integrar CCF exige uma decisao de modelagem da frente 1.

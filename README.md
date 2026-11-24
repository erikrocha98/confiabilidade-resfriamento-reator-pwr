# CCWS - Estudo de Confiabilidade

Trabalho da disciplina de **Confiabilidade de Sistemas** (UFMG).

Estudo de confiabilidade do **CCWS (Component Cooling Water System)** de um
reator PWR Westinghouse. O sistema e modelado por uma arvore de falhas cujo
evento topo e a *perda da funcao de resfriamento do CCWS*, com dois trens
redundantes (A e B) e duas bombas motrizes por trem. Os 24 eventos basicos sao
quantificados com dados de confiabilidade do Idaho National Laboratory (INL) -
ver `dados/fontes.md`.

O trabalho cobre: cortes minimos, probabilidade do evento topo no tempo de
missao, medidas de importancia, simulacao de Monte Carlo, analise de
sensibilidade e comparacao entre a solucao analitica e a simulacao.

> **Estado atual:** arvore e dados de 24 h preenchidos; a frente 3 (solucao
> analitica) esta implementada. As frentes 4 e 5 permanecem em desenvolvimento.

## Frentes de trabalho

| # | Frente | Responsavel | Pasta |
| --- | --- | --- | --- |
| 1 | Modelo e arvore de falhas | [nome] | `modelo/` |
| 2 | Dados (parametros do INL) | [nome] | `dados/` |
| 3 | Solucao analitica (cortes minimos, P(topo), importancias) | [nome] | `analitico/` |
| 4 | Simulacao de Monte Carlo | [nome] | `monte_carlo/` |
| 5 | Sensibilidade e integracao | [nome] | `sensibilidade/` |

Cada pasta tem um `README.md` com responsavel, entradas, saidas esperadas e
dependencias.

## Dependencias entre as frentes

```
   1 (modelo)                     3 (analitico)
       |                        /                \
       +--> 2 (dados) ---------+                  +--> 5 (sensibilidade)
                                \                /
                                  4 (monte carlo)
```

Em texto: **1 → 2 → 3 e 4 → 5**.

- A frente 1 define a arvore; a frente 2 preenche os parametros dos eventos dessa arvore.
- As frentes 3 e 4 consomem modelo + dados e podem trabalhar **em paralelo**.
- A frente 5 consome as **saidas** das frentes 3 e 4, por isso roda por ultimo.

## Estrutura do repositorio

```
.
├── config/         parametros globais (tempo de missao, n de simulacoes, semente)
├── modelo/         frente 1: arvore de falhas (arvore_falhas.yaml)
├── dados/          frente 2: tabelas de parametros do INL + dicionario de dados e fontes
├── ccws/           pacote compartilhado pelas frentes 3, 4 e 5
├── analitico/      frente 3: cortes minimos, probabilidade do topo, importancias
├── monte_carlo/    frente 4: simulacao e convergencia
├── sensibilidade/  frente 5: cenarios e comparacao analitico x Monte Carlo
├── scripts/        utilitarios (validacao dos dados)
├── tests/          testes com pytest
└── docs/           declaracao de uso de IA
```

O pacote `ccws/` concentra o que e comum a todas as frentes:

- `ccws/arvore.py` - carrega `modelo/arvore_falhas.yaml`, lista os eventos basicos
  e avalia a funcao estrutura: `avalia({"MDP_A": True, ...}) -> bool`.
- `ccws/dados.py` - carrega e valida `dados/*.csv` e `config/parametros_globais.yaml`.

As pastas `*/resultados/` guardam as saidas das analises e **nao sao versionadas**
(so a pasta, via `.gitkeep`): quem precisar dos numeros roda os scripts.

## Instalacao

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar

Testes:

```bash
pytest
```

Validacao dos dados (quais eventos da arvore ainda nao tem dados preenchidos):

```bash
python scripts/validar_dados.py
```

Solucao analitica:

```bash
python analitico/cortes_minimos.py
python analitico/probabilidade_topo.py
python analitico/importancia.py
```

Analises ainda em desenvolvimento:

```bash
python monte_carlo/simulacao.py
python monte_carlo/convergencia.py
python sensibilidade/rodar_cenarios.py
python sensibilidade/comparacao.py
```

## Regras do repositorio

1. **Uma branch por frente.** Nomes: `frente-1-modelo`, `frente-2-dados`,
   `frente-3-analitico`, `frente-4-monte-carlo`, `frente-5-sensibilidade`.
   Ninguem comita direto na `main`.
2. **Merge so por pull request revisado por outro integrante.** Quem abre o PR
   nao aprova o proprio PR. Antes de abrir: `pytest` passando.
3. **Nada de dados inventados.** Todo valor numerico em `dados/` precisa de
   `fonte` e `pagina_tabela` apontando para um relatorio do INL (`dados/fontes.md`).
   Valor sem fonte, estimado "de cabeca" ou gerado por IA nao entra no repositorio.
4. **A logica da arvore de falhas e da frente 1.** Mudanca em
   `modelo/arvore_falhas.yaml` exige PR proprio e aviso ao grupo: os ids de
   evento sao a chave dos dados e das cinco frentes.
5. **Parametros globais ficam em `config/parametros_globais.yaml`**, nunca
   fixados dentro do codigo.
6. **Uso de IA deve ser registrado** em `docs/declaracao_uso_ia.md`.

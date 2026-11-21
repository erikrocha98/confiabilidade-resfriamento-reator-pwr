# Frente 4 - Simulacao de Monte Carlo

Responsavel: [nome]

Estima a probabilidade do evento topo por simulacao: sorteia o estado dos 24
eventos basicos no tempo de missao, avalia a funcao estrutura da arvore e conta
a fracao de historias em que o CCWS perde a funcao de resfriamento.

## Entradas

- `modelo/arvore_falhas.yaml` (frente 1), via `ccws.arvore` - a funcao estrutura
  usada aqui e a mesma da frente 3, o que garante que as duas abordagens
  resolvem exatamente o mesmo modelo.
- `dados/parametros_eventos.csv` (frente 2), via `ccws.dados`.
- `config/parametros_globais.yaml` - `tempo_missao_h`, `n_simulacoes`, `semente_aleatoria`.

## Saidas esperadas (em `resultados/`)

| Arquivo | Conteudo |
| --- | --- |
| `mc_resumo.csv` | Estimativa da probabilidade do topo, numero de historias, erro padrao, IC 95%, semente usada. |
| `mc_convergencia.csv` | Curva de convergencia: estimativa e IC em funcao do numero de historias. |
| `mc_convergencia.png` | Grafico de convergencia para o relatorio. |

Os arquivos de `resultados/` nao sao versionados; a pasta fica no repo via `.gitkeep`.

## Depende de

Frentes 1 (modelo) e 2 (dados).

## Arquivos

- `simulacao.py` - sorteio dos estados, avaliacao das historias, estimativa da probabilidade.
- `convergencia.py` - curva de convergencia e justificativa do `n_simulacoes`.

## Decisao pendente desta frente: bomba reserva (spare)

As duas bombas de cada trem aparecem na arvore como uma porta `AND`
(`BOMBAS_A = MDP_A AND MDP_C`), isto e, redundancia ativa: o trem so perde
bombeamento se as duas falharem.

Se o grupo entender que a segunda bomba de cada trem opera como **reserva em
espera**, a simulacao pode precisar de logica de espera (spare): a reserva so e
exigida a partir do instante em que a principal falha, e pode ter probabilidade
de falha na partida / na comutacao diferente da falha durante operacao. Isso
muda o sorteio, nao a arvore.

A decisao e desta frente e precisa ser registrada no relatorio:

- **Opcao A (redundancia ativa):** usar a arvore como esta. Mais simples e
  diretamente comparavel com a solucao analitica da frente 3.
- **Opcao B (reserva em espera):** tratar a dependencia temporal dentro do
  sorteio, em `tratar_bomba_reserva`. Nesse caso a comparacao com a frente 3
  deixa de ser exata e isso tem que ficar explicito na frente 5.

Em qualquer caso, **nao alterar `modelo/arvore_falhas.yaml`** sem combinar com a
frente 1: a logica da arvore e compartilhada por todas as frentes.

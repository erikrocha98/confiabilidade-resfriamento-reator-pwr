# Frente 4 - Simulacao de Monte Carlo

Responsavel: Caue

Estima a probabilidade do evento topo por simulacao: sorteia o estado dos 24
eventos basicos no tempo de missao, avalia a funcao estrutura da arvore e conta
a fracao de historias em que o CCWS perde a funcao de resfriamento.

> **Estado atual:**
> - Modelo base (redundancia ativa, vetorizado em lotes, ICs de Wald/Wilson/Clopper-Pearson);
> - Estudo de convergencia e dimensionamento de `n_simulacoes`;
> - Extensao dinamica (`dinamico.py` + `tratar_bomba_reserva`): bomba em espera
>   (*cold/warm standby*) usando modos decompostos de `dados/extracao_bruta.csv`
>   e motor de Simulação a Eventos Discretos (DES) com reparo parametrizado
>   (MTTR deixado em branco ate definicao de fonte documentada — nenhum valor e
>   inventado).

## Entradas

- `modelo/arvore_falhas.yaml` (frente 1), via `ccws.arvore` - a funcao estrutura
  usada aqui e a mesma da frente 3, o que garante que as duas abordagens
  resolvem exatamente o mesmo modelo.
- `dados/parametros_eventos.csv` (frente 2), via `ccws.dados`.
- `dados/extracao_bruta.csv` (Table 1 do INL), usado por `dinamico.py` para
  separar modos de demanda (`Beta`, ex. `MDP-FTS-CCW`) de taxas horarias
  (`Gamma`, ex. `MDP-FTR-CCW`, `MDP-ELS`, `MDP-ELL`).
- `config/parametros_globais.yaml` - `tempo_missao_h`, `n_simulacoes`, `semente_aleatoria`.

## Saidas esperadas (em `resultados/`)

| Arquivo | Conteudo |
| --- | --- |
| `mc_resumo.csv` | `modelo`, `n_historias`, `n_falhas`, `p_topo`, `erro_padrao`, `erro_relativo`, `nivel_confianca`, `ic95_inf`/`ic95_sup` (Wilson), `ic_wald_*`, `ic_wilson_*`, `ic_clopper_pearson_*`, `semente`, `tempo_missao_h`. |
| `mc_importancias.csv` | Aproximacao empirica de Fussell-Vesely por evento (`falhas_no_topo`, `fussell_vesely_mc`). |
| `mc_convergencia.csv` | Curva de convergencia em grade logaritmica (`n_historias`, `n_falhas`, `estimativa`, `erro_padrao`, `erro_relativo`, `meia_largura_rel_ic95`, ICs). |
| `mc_convergencia.png` | Grafico em 2 paineis: estimativa + IC 95% (Wilson) e erro relativo vs. tendencia teorica $N^{-1/2}$. |
| `mc_dinamico_bombas.csv` | Comparacao do subsistema `BOMBAS_A` (ativa x cold standby x reparo se MTTR fornecido) em 24 h, 720 h e 8760 h. |
| `mc_dinamico_bombas.png` | Grafico comparativo Ativa x Cold Standby em 24 h, 720 h e 8760 h (gerado por `dinamico.py`). |
| `mc_dinamico_topo.csv` | Comparacao de `P(TOPO)` em `tempo_missao_h` entre redundancia ativa e bomba em espera. |

Os arquivos de `resultados/` nao sao versionados; a pasta fica no repo via `.gitkeep`.

## Depende de

Frentes 1 (modelo) e 2 (dados).

## Arquivos

- `simulacao.py` - sorteio dos estados, avaliacao das historias, estimativa da probabilidade.
- `convergencia.py` - curva de convergencia e justificativa do `n_simulacoes`.
- `dinamico.py` - extensao de bomba em espera (standby) e motor DES de reparo parametrizado.
- `relatorio_monte_carlo.md` - rascunho de texto (Materiais e Metodos + Resultados da simulacao).
- `apresentacao_monte_carlo.md` - roteiro de slides e notas de fala da Frente 4.

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

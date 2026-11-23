# Frente 4 — Texto do Relatório (Simulação de Monte Carlo)
---
## Materiais e Métodos — Simulação de Monte Carlo

### 1. Visão geral e arquitetura da simulação

Para complementar a solução analítica da árvore de falhas do *Component Cooling Water System* (CCWS) e avaliar comportamentos temporais que fogem ao modelo estático, foi implementada uma simulação de Monte Carlo em Python (`NumPy`, `SciPy` e `Pandas`) estruturada em dois níveis:

1. **Modelo Base (estático, redundância ativa):** reproduz exatamente a lógica da árvore de falhas definida em `modelo/arvore_falhas.yaml`, garantindo comparabilidade direta com a solução analítica da Frente 3.
2. **Extensão Dinâmica (bomba em espera e reparo):** modela explicitamente a lógica temporal de bomba reserva em espera (*cold/warm standby*) e a Simulação a Eventos Discretos (DES) com reparo, sem alterar a topologia compartilhada da árvore.

Todos os parâmetros globais — tempo de missão ($T = 24\text{ h}$), número de histórias simuladas ($N = 10^6$) e semente do gerador pseudoaleatório (`20262`, via `numpy.random.default_rng`) — são lidos exclusivamente de `config/parametros_globais.yaml`, garantindo total reprodutibilidade dos resultados. A avaliação lógica das histórias utiliza uma compilação vetorizada diretamente das portas `AND`/`OR` de `ccws/arvore.py`, cuja equivalência exata (100% de concordância) foi verificada contra a função estrutura `ArvoreDeFalhas.avalia`. Para permitir a execução de dezenas de milhões de histórias com consumo controlado de memória RAM, as réplicas são processadas em lotes vetorizados de 500.000 histórias.

### 2. Modelo base, estimadores e intervalos de confiança

No modelo base, cada um dos 24 eventos básicos $E_i$ recebe sua probabilidade de falha na missão $p_i$ proveniente de `dados/parametros_eventos.csv` (combinando os modos de falha aplicáveis da Table 1 do relatório INL/EXT-21-65055 para $T = 24\text{ h}$). Em cada história $j \in \{1, \dots, N\}$:

1. Sorteia-se o vetor binário de estados $\mathbf{x}^{(j)} \in \{0,1\}^{24}$, com $x_i^{(j)} \sim \text{Bernoulli}(p_i)$ independentes.
2. Avalia-se a função estrutura do sistema $y^{(j)} = \phi(\mathbf{x}^{(j)}) \in \{0, 1\}$, onde $y^{(j)} = 1$ indica ocorrência do evento topo (*perda da função de resfriamento do CCWS*).

Contabilizando $k = \sum_{j=1}^{N} y^{(j)}$ falhas do evento topo em $N$ histórias, a estimativa pontual de probabilidade, o erro padrão ($\text{SE}$) e o erro relativo são dados por:

- $\hat{p} = k / N$
- $\text{SE} = \sqrt{\hat{p}(1 - \hat{p}) / N}$
- $\text{Erro relativo} = \text{SE} / \hat{p}$

Como a perda simultânea dos dois trens redundantes do CCWS configura um **evento raro** (ordem de $10^{-5}$ em 24 h), o número esperado de ocorrências $k$ em $10^6$ histórias é pequeno, situação em que o intervalo de confiança normal clássico de **Wald** ($\hat{p} \pm z_{1-\alpha/2}\,\text{SE}$) apresenta assimetria subestimada e cobertura inferior à nominal. Por essa razão, adotou-se como intervalo principal de 95% o **intervalo de escore de Wilson**:

$$\text{IC}_{95\%,\text{Wilson}} = \frac{\hat{p} + \frac{z^2}{2N} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}$$

reportando-se também os intervalos de **Wald** e **Clopper-Pearson** (exato binomial) para transparência metodológica. Adicionalmente, estimou-se a contribuição empírica de cada evento básico para a falha do topo via aproximação de Fussell-Vesely por Monte Carlo, $\widehat{\text{FV}}_i = P(E_i = 1 \mid \text{TOPO} = 1)$.

### 3. Estudo de convergência e dimensionamento amostral

A convergência da simulação foi acompanhada avaliando-se a estimativa acumulada $\hat{p}_n$, o erro relativo e os limites do IC 95% ao longo de uma grade logarítmica de checkpoints $n \in [10^3, N]$, utilizando a mesma divisão de lotes e a mesma semente do modelo base.

O critério de convergência adotado define o número mínimo de histórias necessário como o menor $n$ a partir do qual o erro relativo permanece igual ou inferior à meta $\varepsilon$ até o fim da corrida (evitando falsos positivos em oscilações iniciais). Para embasar o dimensionamento de `n_simulacoes`, os resultados observados foram confrontados com a expressão binomial teórica:

- Para controle do erro padrão relativo ($\text{SE}/p \le \varepsilon$): $N \ge \dfrac{1 - p}{p\,\varepsilon^2}$
- Para controle da meia-largura relativa do IC 95% ($\le \pm \varepsilon$): $N \ge \dfrac{z_{0{,}975}^2\,(1 - p)}{p\,\varepsilon^2}$

### 4. Modelagem dinâmica: bomba em espera (standby) e reparo (DES)

Na árvore estática, as duas bombas motrizes de cada trem formam uma porta `AND` (`BOMBAS_A = MDP_A AND MDP_C` e `BOMBAS_B = MDP_B AND MDP_D`), correspondendo a **redundância ativa**. Para avaliar a operação em **reserva em espera fria (*cold standby*)**, os modos de falha da bomba motriz (`MDP`) foram decompostos a partir da Table 1 de `dados/extracao_bruta.csv` (INL/EXT-21-65055):

- **Falha sob demanda na partida:** `MDP-FTS-CCW` (distribuição Beta), com média $q_{\text{FTS}} = 4{,}570 \times 10^{-4}$ por demanda.
- **Taxa de falha em operação contínua:** soma dos modos `MDP-FTR-CCW` ($1{,}77 \times 10^{-6}\text{ h}^{-1}$), `MDP-ELS` ($1{,}98 \times 10^{-7}\text{ h}^{-1}$) e `MDP-ELL` ($1{,}39 \times 10^{-8}\text{ h}^{-1}$), totalizando $\lambda_{\text{op}} = 1{,}9819 \times 10^{-6}\text{ h}^{-1}$.

Em cada trem, a bomba reserva permanece inativa (sem desgaste operacional em espera fria) até o instante $t_1$ em que a bomba principal falha. Se $t_1 < T$, a reserva sofre uma demanda de partida com probabilidade de falha $q_{\text{FTS}}$; caso parta com sucesso, passa a operar pelo tempo residual $T - t_1$ com tempo até falha exponencial de taxa $\lambda_{\text{op}}$. Foram analisados dois regimes físicos para a bomba principal:

1. **Principal já em operação contínua em $t = 0$** (configuração típica de operação normal do CCWS de um PWR, na qual uma bomba já roda continuamente e apenas a reserva é demandada em caso de falha);
2. **Principal sujeita a demanda de partida em $t = 0$** (cenário conservador, diretamente alinhado à inclusão de `MDP-FTS-CCW` na probabilidade de missão estática).

Para incorporar **reparo**, implementou-se um motor de **Simulação a Eventos Discretos (DES)** que acompanha os eventos de falha e término de reparo (tempos exponenciais com média $\text{MTTR}$ e política configurável de 1 ou 2 equipes de manutenção) em $[0, T]$, calculando a não-confiabilidade na missão $F(T)$, a indisponibilidade pontual $U(T)$ e a indisponibilidade média $\bar{U}(T)$. A correção matemática do código foi verificada por suíte automatizada (`pytest`, 68 testes) contra: (i) a solução analítica fechada da espera fria sem reparo (convolução exponencial/Erlang) e (ii) a matriz exponencial de uma Cadeia de Markov Contínua de 3 estados para o modelo com reparo (1 e 2 equipes).

> **Nota sobre dados de reparo (MTTR):** Em conformidade com a diretriz do trabalho de não empregar parâmetros estimados arbitrariamente, o motor DES exige que qualquer valor de MTTR seja fornecido com fonte e página/tabela documentadas. Como os relatórios do INL extraídos até o momento não fornecem MTTR para os componentes do CCWS, os resultados numéricos de simulação dinâmica abaixo referem-se ao cenário sem reparo (*cold standby*), mantendo-se o motor de reparo pronto para execução imediata mediante fornecimento de tabela validada (`--mttr-csv`). *[Atualizar este parágrafo caso o grupo incorpore uma referência bibliográfica de MTTR.]*

---

## Resultados — Simulação de Monte Carlo

### 1. Probabilidade do evento topo — Caso Base ($T = 24\text{ h}$)

A Tabela 1 resume os resultados da simulação de Monte Carlo no modelo base (redundância ativa), executada com $N = 1.000.000$ de histórias e semente `20262`.

**Tabela 1 — Resumo da estimativa de Monte Carlo para o evento topo do CCWS ($T = 24\text{ h}$, modelo base).**

| Métrica | Valor obtido |
| --- | --- |
| Modelo | Redundância ativa (árvore estática) |
| Tempo de missão ($T$) | 24 h |
| Histórias simuladas ($N$) | 1.000.000 |
| Semente aleatória | 20262 |
| Falhas do evento topo observadas ($k$) | 11 |
| Probabilidade estimada $\hat{P}(\text{TOPO})$ | **1,1000 × 10⁻⁵** |
| Erro padrão ($\text{SE}$) | 3,3166 × 10⁻⁶ |
| Erro relativo ($\text{SE} / \hat{p}$) | 30,15% |
| IC 95% — Wilson (padrão) | **[6,1424 × 10⁻⁶ ; 1,9699 × 10⁻⁵]** |
| IC 95% — Wald (aproximação normal) | [4,4996 × 10⁻⁶ ; 1,7500 × 10⁻⁵] |
| IC 95% — Clopper-Pearson (exato binomial) | [5,4912 × 10⁻⁶ ; 1,9682 × 10⁻⁵] |

A estimativa pontual obtida ($\hat{P}(\text{TOPO}) = 1{,}10 \times 10^{-5}$) mostra-se estatisticamente compatível com o valor analítico de referência *[inserir valor exato da Frente 3 — ordem esperada de ~1,30 × 10⁻⁵]*, que se encontra confortavelmente contido nos intervalos de confiança de 95% de Wilson e Clopper-Pearson. Nota-se também a importância da escolha do estimador de intervalo em regime de evento raro: com apenas $k = 11$ ocorrências, o intervalo de Wald subestima a cauda superior (`1,75 × 10⁻⁵` frente a `1,97 × 10⁻⁵` em Wilson e Clopper-Pearson).

### 2. Análise de convergência e dimensionamento de $N$

A Figura 1 apresenta a evolução acumulada da estimativa $\hat{P}(\text{TOPO})$, a faixa do IC 95% de Wilson e o comportamento do erro relativo ($\text{SE}/\hat{p}$) em função do número de histórias simuladas.

![Curva de convergência da simulação de Monte Carlo do CCWS](resultados/mc_convergencia.png)
*Figura 1 — Convergência da estimativa de $P(\text{TOPO})$ (painel superior, com faixa de IC 95% de Wilson) e decaimento do erro relativo $\text{SE}/\hat{p}$ frente à tendência teórica proporcional a $N^{-1/2}$ (painel inferior), para $N = 10^6$ histórias e semente `20262`.*

Observa-se que a primeira falha do evento topo ocorre somente após aproximadamente $3{,}3 \times 10^4$ histórias, gerando inicialmente um erro relativo de 100%. A partir de $3 \times 10^5$ histórias, o acúmulo de ocorrências estabiliza a estimativa na faixa de $1{,}0\text{–}1{,}4 \times 10^{-5}$, acompanhando fielmente a inclinação teórica $O(N^{-1/2})$.

Contudo, ao término de $N = 10^6$ histórias, o erro relativo permanece em **30,15%** (meia-largura relativa do IC 95% de **61,62%**), sem atingir metas típicas de 10% ou 5%. A Tabela 2 sintetiza o dimensionamento teórico obtido pela fórmula binomial para $\hat{p} = 1{,}10 \times 10^{-5}$.

**Tabela 2 — Dimensionamento do número de histórias ($N$) para diferentes metas de precisão em Monte Carlo bruto.**

| Critério de precisão | Observado em $N = 10^6$ | $N$ teórico estimado |
| --- | --- | ---: |
| Erro padrão relativo ($\text{SE}/\hat{p} \le 10\%$) | Não atingido (atual: 30,15%) | ~9,09 × 10⁶ |
| Erro padrão relativo ($\text{SE}/\hat{p} \le 5\%$) | Não atingido | ~3,64 × 10⁷ |
| Meia-largura IC 95% ($\le \pm 10\%$) | Não atingido (atual: 61,62%) | ~3,49 × 10⁷ |
| Meia-largura IC 95% ($\le \pm 5\%$) | Não atingido | ~1,40 × 10⁸ |

Esse resultado quantifica o principal desafio computacional do Monte Carlo bruto em sistemas nucleares altamente redundantes: confirmar a ordem de grandeza de $P(\text{TOPO}) \sim 10^{-5}$ é viável com $10^6$ histórias, mas obter precisão inferior a 10% no erro padrão (ou no IC 95%) requer entre $10^7$ e $3{,}5 \times 10^7$ histórias — ou o emprego de técnicas de redução de variância.

### 3. Efeito da bomba em espera (*cold standby*) no subsistema e no sistema completo

Para avaliar isoladamente o impacto da estratégia de operação das bombas motrizes, a Tabela 3 e a Figura 2 comparam a redundância ativa com os dois regimes de *cold standby* para o subsistema `BOMBAS_A` (par `MDP_A` e `MDP_C`, sem reparo) em três horizontes: 24 h (missão base), 720 h (30 dias) e 8.760 h (1 ano), sempre com $N = 10^6$ histórias.

**Tabela 3 — Comparação entre redundância ativa e *cold standby* no subsistema `BOMBAS_A` (1+1 bombas, sem reparo, $N = 10^6$).**

| Horizonte | Modelo do par de bombas | Falhas MC ($k$) | $\hat{P}$ (Monte Carlo) | IC 95% Wilson | $P$ analítica ref. |
| --- | --- | ---: | ---: | --- | ---: |
| 24 h | Redundância ativa | 1 | 1,00 × 10⁻⁶ | [1,77 × 10⁻⁷ ; 5,66 × 10⁻⁶] | 2,55 × 10⁻⁷ |
| 24 h | Cold standby (principal parte em $t=0$) | 0 | 0,00 | [0,00 ; 3,84 × 10⁻⁶] | 2,53 × 10⁻⁷ |
| 24 h | Cold standby (principal já operando) | 0 | 0,00 | [0,00 ; 3,84 × 10⁻⁶] | **2,29 × 10⁻⁸** |
| 720 h | Redundância ativa | 2 | 2,00 × 10⁻⁶ | [5,48 × 10⁻⁷ ; 7,29 × 10⁻⁶] | 3,54 × 10⁻⁶ |
| 720 h | Cold standby (principal parte em $t=0$) | 0 | 0,00 | [0,00 ; 3,84 × 10⁻⁶] | 2,53 × 10⁻⁶ |
| 720 h | Cold standby (principal já operando) | 2 | 2,00 × 10⁻⁶ | [5,48 × 10⁻⁷ ; 7,29 × 10⁻⁶] | **1,67 × 10⁻⁶** |
| 8.760 h | Redundância ativa | 308 | 3,08 × 10⁻⁴ | [2,75 × 10⁻⁴ ; 3,44 × 10⁻⁴] | 3,12 × 10⁻⁴ |
| 8.760 h | Cold standby (principal parte em $t=0$) | 154 | 1,54 × 10⁻⁴ | [1,32 × 10⁻⁴ ; 1,80 × 10⁻⁴] | 1,65 × 10⁻⁴ |
| 8.760 h | Cold standby (principal já operando) | 156 | 1,56 × 10⁻⁴ | [1,33 × 10⁻⁴ ; 1,82 × 10⁻⁴] | **1,57 × 10⁻⁴** |

![Comparação entre redundância ativa e cold standby no subsistema BOMBAS_A](resultados/mc_dinamico_bombas.png)
*Figura 2 — Comparação entre redundância ativa e espera fria (cold standby) no subsistema `BOMBAS_A` em três horizontes temporais (esquerda, escala logarítmica) e validação direta entre Monte Carlo ($N = 10^6$, IC 95% de Wilson) e solução analítica fechada em 8.760 h (direita).*

Os resultados revelam três conclusões físicas importantes:

1. **Regime de missão curta (24 h) — dominância da falha na partida:** quando a bomba principal também sofre demanda de partida em $t = 0$, a espera fria praticamente iguala a redundância ativa ($2{,}53 \times 10^{-7}$ vs. $2{,}55 \times 10^{-7}$), pois a probabilidade de falha na partida ($q_{\text{FTS}} = 4{,}57 \times 10^{-4}$) é quase uma ordem de grandeza superior à probabilidade de falha em operação durante 24 h ($\lambda_{\text{op}} T \approx 4{,}76 \times 10^{-5}$). Já no regime operacional normal de PWR (bomba principal já em funcionamento contínuo e apenas a reserva sob demanda), o *cold standby* reduz a probabilidade de perda de bombeamento em cerca de **11 vezes** (para $2{,}29 \times 10^{-8}$).
2. **Horizonte longo (8.760 h = 1 ano) — redução de 50% validada por Monte Carlo:** quando o termo de operação contínua passa a dominar ($\lambda_{\text{op}} T \approx 1{,}74 \times 10^{-2}$), a reserva em espera fria reduz à metade a probabilidade de falha do par de bombas — exatamente conforme a relação teórica $\frac{1}{2}(\lambda T)^2$ versus $(\lambda T)^2$. As estimativas de Monte Carlo (`308`, `154` e `156` falhas) concordam rigorosamente com os valores analíticos fechados dentro do IC 95%.
3. **Impacto no evento topo do CCWS em 24 h:** ao substituir o subsistema de bombas por *cold standby* na simulação do sistema completo (mantendo a mesma semente nos demais 20 eventos básicos), os três modelos apresentaram exatamente o mesmo resultado: **11 falhas em $10^6$ histórias** ($\hat{P}(\text{TOPO}) = 1{,}10 \times 10^{-5}$, IC 95% Wilson $[6{,}14 \times 10^{-6}; 1{,}97 \times 10^{-5}]$). Isso ocorre porque cada trem possui dez componentes em série (instrumentação, válvulas, trocador de calor e tubulação) cuja probabilidade combinada de falha é de $\sim 3{,}60 \times 10^{-3}$ — **quatro a cinco ordens de grandeza maior** que a probabilidade de falha simultânea das duas bombas ($\sim 10^{-8}\text{–}10^{-7}$). Consequentemente, em missões de 24 h sem falhas de causa comum (CCF), o risco do CCWS é dominado pelos componentes em série de cada trem, preservando plena compatibilidade prática entre a simulação com bomba em espera e a solução analítica da Frente 3.

*[Espaço reservado — Reparo (DES): caso o grupo obtenha valores documentados de MTTR na literatura (INL/NUREG), executar `python monte_carlo/dinamico.py --mttr-csv <arquivo.csv>` e acrescentar aqui a comparação de $F(T)$ e $\bar{U}(T)$ com e sem reparo.]*

# Roteiro da apresentacao - frente analitica

Sugestao de **2 slides** dentro da apresentacao de 10 minutos. Tempo total da
frente: aproximadamente 2 minutos.

## Slide 1 - Cortes minimos e probabilidade do topo

**Mensagem principal:** a redundancia dos dois trens faz com que nao exista
corte de ordem 1.

- 121 cortes minimos: 100 de ordem 2, 20 de ordem 3 e 1 de ordem 4.
- Exibir tres exemplos:
  - ordem 2: `{STL_A, MOV_B}`;
  - ordem 3: `{MDP_A, MDP_C, MOV_B}`;
  - ordem 4: `{MDP_A, MDP_C, MDP_B, MDP_D}`.
- Missao de 24 h, independencia entre eventos:
  - `P(topo) = 1,2977 x 10^-5`;
  - `R = 99,998702%`;
  - limite por eventos raros apenas 0,298% acima do exato.

**Fala sugerida:** “O sistema so falha quando os dois trens falham. Por isso,
os menores cortes combinam um evento em serie de cada trem. Calculamos a uniao
exata dos 121 cortes e usamos a soma das probabilidades apenas como verificacao.”

## Slide 2 - Ranking de componentes

Usar a figura `resultados/ranking_fussell_vesely.png`.

**Destaques:**

- STL e STF lideram: `I_FV = 0,2263` por evento.
- Depois aparecem MOV (`0,1777`), XVM (`0,1454`) e STT (`0,1251`).
- Eventos equivalentes dos trens A e B empatam por simetria dos dados.
- Bombas MDP ficam no fim do ranking, pois duas bombas do mesmo trem precisam
  falhar para derrubar o bombeamento.

**Fala sugerida:** “Fussell-Vesely combina a estrutura da arvore com a
probabilidade atual e e a medida mais clara para priorizacao. Birnbaum mede a
sensibilidade marginal; entre os itens em serie, seus valores ficam quase
iguais.”

## Nota obrigatoria no rodape ou na fala

“Resultado-base para 24 h, sob independencia. Os fatores de causa comum das
bombas foram levantados, mas ainda nao estao integrados a arvore; horizontes de
1 a 40 anos exigem recomputar os modos de falha, nao extrapolar o valor de 24 h.”

## Perguntas provaveis do professor

**Por que a soma dos cortes nao e o resultado exato?**
Porque cortes diferentes compartilham eventos; somar suas probabilidades conta
as intersecoes mais de uma vez. A expansao de Shannon calcula a uniao exata.

**Por que as bombas nao aparecem entre as mais importantes?**
Cada trem tem duas bombas em paralelo logico: o evento `BOMBAS_X` e uma porta
AND. Uma bomba isolada nao derruba o trem.

**A CCF pode mudar o resultado?**
Sim. Uma CCF pode reduzir o beneficio da redundancia e elevar a importancia das
bombas. Ela deve entrar como eventos explicitos na arvore antes da quantificacao.

**O resultado prova confiabilidade de 99% por 40 anos?**
Nao. Ele responde apenas a missao de 24 h. O teste de horizontes longos ainda
depende da recombinacao temporal dos modos de falha e da definicao de reparo.

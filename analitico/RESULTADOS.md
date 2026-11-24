# Resultados - solucao analitica

> Texto-base para revisao e adaptacao pelos autores. Os numeros abaixo sao
> reproduziveis pelos scripts da pasta `analitico/` e se referem a missao de
> 24 h. Este texto nao substitui a interpretacao e a conclusao do grupo.

## Metodo de calculo

Os cortes minimos foram obtidos por expansao recursiva da arvore de falhas. Em
uma porta OR, os cortes das entradas foram reunidos; em uma porta AND, foi
realizado o produto cartesiano entre os cortes das entradas. Em cada etapa,
aplicou-se a regra de absorcao para remover conjuntos nao minimos. Todos os
cortes resultantes foram verificados na funcao estrutura: a ocorrencia de todos
os eventos do corte deve causar o evento topo, enquanto a retirada de qualquer
evento deve impedir sua ocorrencia.

Para cada evento basico foi usada a probabilidade agregada de falha em 24 h da
frente 2. Sob a hipotese de independencia, a probabilidade exata do evento topo
foi calculada como a uniao dos cortes minimos, por expansao de Shannon. Como
comparacao, foi calculado o limite superior de Boole, equivalente a soma das
probabilidades dos cortes na aproximacao de eventos raros.

As importancias foram avaliadas por:

- Birnbaum: `I_B(i) = P(T | i=1) - P(T | i=0)`;
- Fussell-Vesely: `I_FV(i) = [P(T) - P(T | i=0)] / P(T)`.

Tambem foram calculados RAW e RRW como resultados auxiliares.

## Cortes minimos

A arvore produziu **121 cortes minimos**:

| Ordem | Quantidade | Estrutura |
| ---: | ---: | --- |
| 2 | 100 | um evento em serie do trem A e um do trem B |
| 3 | 20 | o par de bombas de um trem e um evento em serie do outro |
| 4 | 1 | `MDP_A, MDP_C, MDP_B, MDP_D` |

Os cortes de ordem 2 dominam numericamente e representam diretamente a perda
simultanea dos dois trens por componentes que, dentro de cada trem, estao em
serie. O unico corte de ordem 4 corresponde a perda das duas bombas de cada
trem.

## Probabilidade do evento topo

Para missao de 24 h, foram obtidos:

| Metrica | Valor |
| --- | ---: |
| Probabilidade exata do evento topo | `1,297671 x 10^-5` |
| Confiabilidade do sistema | `0,9999870233` (99,998702%) |
| Limite superior pelos cortes | `1,301542 x 10^-5` |
| Excesso relativo do limite superior | `0,2983%` |

O limite superior ficou proximo do resultado exato, o que confirma que a
aproximacao de eventos raros e adequada para uma estimativa rapida neste
horizonte. O valor exato foi mantido como resultado principal porque considera
as intersecoes entre os cortes e elimina a dupla contagem.

## Importancia dos componentes

Como os trens usam as mesmas probabilidades, os eventos equivalentes dos trens
A e B apresentam importancias iguais, salvo arredondamento numerico.

| Posicao (grupo) | Eventos | Prob. em 24 h | Fussell-Vesely | Birnbaum |
| ---: | --- | ---: | ---: | ---: |
| 1 | `STL_A/B`, `STF_A/B` | `8,1745 x 10^-4` | `0,226291` | `3,59228 x 10^-3` |
| 2 | `MOV_A/B` | `6,4195 x 10^-4` | `0,177677` | `3,59165 x 10^-3` |
| 3 | `XVM_A/B` | `5,2532 x 10^-4` | `0,145379` | `3,59123 x 10^-3` |
| 4 | `STT_A/B` | `4,5215 x 10^-4` | `0,125121` | `3,59097 x 10^-3` |
| 5 | `STP_A/B` | `1,3673 x 10^-4` | `0,037825` | `3,58983 x 10^-3` |
| 6 | `CKV_A/B` | `1,3610 x 10^-4` | `0,037650` | `3,58983 x 10^-3` |

STL e STF lideram o ranking de Fussell-Vesely porque combinam a maior
probabilidade individual com uma posicao em serie dentro de cada trem. MOV,
XVM e STT aparecem em seguida pelo mesmo mecanismo. As quatro bombas MDP,
apesar de terem probabilidade individual de `5,0454 x 10^-4`, ocupam as ultimas
posicoes (`I_FV = 7,0411 x 10^-5`), pois a falha de apenas uma bomba nao derruba
o trem: e necessaria a falha simultanea do par.

Os valores de Birnbaum dos componentes em serie sao muito proximos porque a
medida expressa a sensibilidade estrutural do topo a uma alteracao marginal na
probabilidade do evento. Ja Fussell-Vesely incorpora a probabilidade atual do
evento e, por isso, produz um ranking mais discriminante para priorizacao.

## Limitacoes que devem acompanhar os resultados

1. **Independencia:** os valores acima nao incluem falhas de causa comum. Os
   fatores alfa de bombas existem em `dados/fatores_alfa_ccf.csv`, mas a arvore
   ainda nao possui eventos CCF. Inclui-los sem alterar a arvore seria
   inconsistente com a funcao estrutura validada.
2. **Horizonte:** os resultados valem para 24 h. Nao se deve extrapolar a
   probabilidade agregada para anos. Os modos por demanda e por taxa devem ser
   recombinados para cada novo tempo usando `dados/extracao_bruta.csv`.
3. **Dados:** STF usa os dados de STL conforme a nota do relatorio do INL; o
   comprimento de PIPE por trem e uma suposicao documentada pela frente 2.
4. **Escopo:** sistemas de suporte e indisponibilidades por teste/manutencao nao
   aparecem na arvore atual.

## Reproducao

```bash
python analitico/cortes_minimos.py
python analitico/probabilidade_topo.py
python analitico/importancia.py
pytest -q
```

# Frente 2 - Dados

Responsavel: [nome]

Tabelas com os parametros de confiabilidade dos eventos basicos da arvore de
falhas do CCWS, extraidos **manualmente** dos relatorios do Idaho National
Laboratory (ver `fontes.md`).

> **Regra da disciplina:** nenhum valor numerico pode ser inventado, estimado
> "de cabeca" ou gerado por ferramenta de IA. Toda celula numerica precisa ter
> `fonte` e `pagina_tabela` apontando para o relatorio de onde saiu. Celula sem
> fonte conta como celula vazia.

## Entradas

- `modelo/arvore_falhas.yaml` - define quais ids de evento precisam existir aqui.
- Relatorios do INL (PDFs, nao versionados no repo - ver `fontes.md`).

## Saidas esperadas

- `parametros_eventos.csv` preenchido para os 24 eventos basicos da arvore.
- `fatores_alfa_ccf.csv` preenchido para os grupos sujeitos a falha de causa comum (CCF).
- `fontes.md` atualizado com a referencia completa de cada relatorio usado.

## Depende de

Frente 1 (modelo), porque os ids de `id_evento` vem da arvore de falhas.

## Como conferir o progresso

```bash
python scripts/validar_dados.py
```

O script lista os eventos da arvore que ainda nao tem linha preenchida.

---

## Dicionario de dados - `parametros_eventos.csv`

Uma linha por evento basico da arvore.

| Coluna | Tipo | Unidade | Descricao |
| --- | --- | --- | --- |
| `id_evento` | texto | - | Id do evento basico, **exatamente** como em `modelo/arvore_falhas.yaml` (ex.: `MDP_A`, `STL_B`). Chave da tabela, nao repete. |
| `trem` | texto | - | Trem redundante do CCWS: `A` ou `B`. |
| `componente` | texto | - | Sigla do componente: `STL`, `STP`, `STT`, `STF`, `PIPE`, `MOV`, `XVM`, `CKV`, `FCV`, `HTX`, `MDP`. |
| `codigo_inl` | texto | - | Codigo do componente/modo de falha como aparece no relatorio do INL, copiado literalmente. |
| `modo_falha` | texto | - | Modo de falha do INL (ex.: falha ao partir, falha ao operar, falha ao abrir). Copiar a nomenclatura do relatorio. |
| `tipo` | texto | - | `demanda` (probabilidade por demanda) ou `taxa` (taxa de falha por unidade de tempo). Define como a frente 3 calcula `prob_missao`. |
| `distribuicao` | texto | - | Distribuicao da incerteza do parametro: `beta`, `gama` ou `lognormal`. Usada pela frente 4 (Monte Carlo) e pela frente 5. |
| `param_alfa` | numero | - | Primeiro parametro da distribuicao: `alfa` da beta, `alfa` (forma) da gama, `mu` da lognormal. |
| `param_beta` | numero | - | Segundo parametro: `beta` da beta, `beta` (escala/taxa, conforme `observacao`) da gama, `sigma` da lognormal. |
| `media` | numero | ver `unidade` | Valor medio do parametro conforme o INL. Para `tipo=demanda` e adimensional; para `tipo=taxa` esta em `unidade`. |
| `p05` | numero | ver `unidade` | Percentil 5% do parametro, quando o relatorio informa. |
| `p95` | numero | ver `unidade` | Percentil 95% do parametro, quando o relatorio informa. |
| `unidade` | texto | - | Unidade de `media`, `p05` e `p95`. Convencao: `adimensional` para demanda; `1/h` para taxas horarias. Nao misturar `1/h` e `1/ano` na mesma tabela. |
| `prob_missao` | numero | adimensional | Probabilidade de falha do evento no tempo de missao (`config/parametros_globais.yaml`). **Calculada pela frente 3**, nao extraida do relatorio: deixar vazia na extracao. |
| `fonte` | texto | - | Identificador curto do relatorio, igual ao usado em `fontes.md` (ex.: `INL/EXT-21-65055`, `CCF-2020-Rev1`). |
| `pagina_tabela` | texto | - | Pagina e/ou numero da tabela de onde o valor foi lido (ex.: `p. 112, Tabela A-3`). |
| `observacao` | texto | - | Qualquer ressalva: parametrizacao da gama usada, valor agrupado, conversao de unidade feita, criterio de escolha quando o relatorio traz mais de uma linha. |

### Convencoes

- Separador decimal: **ponto** (`1.2E-5`, nao `1,2E-5`).
- Notacao cientifica em maiuscula ou minuscula, ambas aceitas (`3.4e-6`).
- Celula sem valor: deixar **vazia**, nunca `0`, `-`, `N/A` ou `nan`.
- Nao reordenar nem renomear colunas: `ccws/dados.py` valida o cabecalho e falha se mudar.

---

## Dicionario de dados - `fatores_alfa_ccf.csv`

Uma linha por grupo de falha de causa comum (modelo de fatores alfa).

| Coluna | Tipo | Unidade | Descricao |
| --- | --- | --- | --- |
| `componente` | texto | - | Sigla do componente do grupo CCF (ex.: `MDP`, `MOV`). |
| `codigo_inl` | texto | - | Codigo do grupo no relatorio de CCF do INL. |
| `modo_falha` | texto | - | Modo de falha a que os fatores alfa se referem. |
| `tamanho_grupo` | numero inteiro | - | Numero de componentes redundantes do grupo (ex.: `4` para as quatro bombas MDP). |
| `alfa_1` | numero | adimensional | Fracao de eventos que afetam exatamente 1 componente. |
| `alfa_2` | numero | adimensional | Fracao que afeta exatamente 2 componentes. |
| `alfa_3` | numero | adimensional | Fracao que afeta exatamente 3 componentes. Vazio se `tamanho_grupo < 3`. |
| `alfa_4` | numero | adimensional | Fracao que afeta exatamente 4 componentes. Vazio se `tamanho_grupo < 4`. |
| `teste_escalonado` | texto | - | `sim` se o relatorio traz os fatores para esquema de teste escalonado (staggered testing), `nao` para teste simultaneo (non-staggered). Os dois conjuntos sao diferentes: nao misturar na mesma linha. |
| `fonte` | texto | - | Igual ao campo `fonte` da outra tabela. |
| `pagina_tabela` | texto | - | Pagina e/ou tabela de origem. |
| `observacao` | texto | - | Ressalvas (grupo mapeado para um subconjunto do CCWS, fatores renormalizados, etc.). |

### Convencoes

- Os `alfa_k` preenchidos devem somar aproximadamente 1 dentro do `tamanho_grupo`;
  se nao somarem, registrar o motivo em `observacao`.
- `alfa_k` com `k > tamanho_grupo` fica vazio.

# Frente 1 - Modelo e arvore de falhas

Responsavel: [nome]

Define o modelo logico do estudo: o que e falha do sistema, quais sao os
eventos basicos e como eles se combinam. Esta frente ja esta concluida -
o arquivo `arvore_falhas.yaml` e a referencia unica para todas as outras.

## Entradas

- Descricao do CCWS (Component Cooling Water System) de um reator PWR Westinghouse:
  dois trens redundantes, quatro bombas motrizes (duas por trem), trocador de
  calor, valvulas e instrumentacao por trem.
- Nomenclatura de componentes compativel com os relatorios do INL (ver `dados/fontes.md`).

## Saidas esperadas

- `arvore_falhas.yaml` - portas logicas e eventos basicos (ja entregue).
- Figura da arvore de falhas para o relatorio final (gerada fora do repo; o PDF
  nao e versionado, ver `.gitignore`).

## Depende de

Nada. E a frente de partida.

## Logica da arvore (nao alterar sem avisar o grupo)

```
TOPO  (AND)  = Perda da funcao de resfriamento do CCWS
├── TREM_A (OR)
│   ├── INSTRUMENTACAO_A (OR) = STL_A, STP_A, STT_A
│   ├── STF_A
│   ├── BOMBAS_A (AND) = MDP_A, MDP_C
│   ├── PIPE_A
│   ├── VALVULAS_A (OR) = MOV_A, XVM_A, CKV_A, FCV_A
│   └── HTX_A
└── TREM_B (OR)
    ├── INSTRUMENTACAO_B (OR) = STL_B, STP_B, STT_B
    ├── STF_B
    ├── BOMBAS_B (AND) = MDP_B, MDP_D
    ├── PIPE_B
    ├── VALVULAS_B (OR) = MOV_B, XVM_B, CKV_B, FCV_B
    └── HTX_B
```

- **24 eventos basicos**: 10 por trem (`STL`, `STP`, `STT`, `STF`, `PIPE`, `MOV`,
  `XVM`, `CKV`, `FCV`, `HTX`) mais as quatro bombas `MDP_A`, `MDP_B`, `MDP_C`, `MDP_D`.
- O topo e um `AND`: o sistema so perde a funcao se **os dois trens** falharem.
- Cada trem e um `OR`: qualquer subsistema derruba o trem.
- As bombas de um trem estao em `AND`: o trem perde bombeamento so se as duas falharem.

## Qualquer mudanca na arvore

Mudar portas, entradas ou ids de evento invalida cortes minimos, probabilidade
do topo, as corridas de Monte Carlo e os cenarios de sensibilidade. Se for
realmente necessario:

1. Abrir uma branch e um pull request descrevendo a mudanca.
2. Avisar as frentes 2 a 5 (ids de evento sao a chave de `dados/parametros_eventos.csv`).
3. Rodar `pytest` - o teste de contagem de eventos basicos vai falhar e precisa ser atualizado junto.

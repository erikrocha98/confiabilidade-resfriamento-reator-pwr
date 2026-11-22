# Conferência manual dos dados extraídos

Este arquivo lista, para cada evento da árvore, o valor de cada modo de falha e a página de onde ele saiu. Serve para conferir à mão contra os PDFs em `docs/`.

- **Como foi gerado:** os valores foram extraídos com IA (Claude Code), usando scripts Python com pypdf; veja `docs/declaracao_uso_ia.md`. Por isso **cada linha precisa ser conferida por um integrante**: marque `[x]` depois de conferir.
- **Páginas:** "PDF" é a página física do arquivo e "impressa" é o número que aparece na página (ver `dados/mapa_relatorio.md`).
- **Fonte dos valores:** a Table 1 do INL/EXT-21-65055. A coluna "Conferir também" aponta a mesma linha no Apêndice A, que deve bater. A Table 1 tem α e β com mais casas decimais.
- **Cálculo:** P_i = média, para falha sob demanda (Beta); P_i = 1 − exp(−λ·t), para taxa (Gamma), com t = 24 h. A probabilidade do evento é prob_missao = 1 − ∏(1 − P_i).
- **Suposição para PIPE:** λ é por hora-pé, e o comprimento usado foi 4008 ft ÷ 2 trens = 2004 ft por trem (ver `dados/README.md`).

## Itens marcados "conferir"

- [ ] **MDP-FTS-CCW**, Table 1 (PDF 32, impressa 8): distribuição Beta (prob. por demanda), mas a coluna d/h da Table 1 indica "h"; Table 44 (PDF 86) e Table 45 (PDF 92) indicam demandas (d), provável erro de digitação na Table 1
- [ ] **PIPE-OTHER-ELL**, Table 1 (PDF 38, impressa 14): p05 diverge entre Table 1 (PDF 38: 2.70E-15) e Table 177 (PDF 181: 2.71E-15)
- [ ] **PIPE-OTHER-ELL**, Table 177 (PDF 181, impressa A-122): p05 diverge entre Table 1 (PDF 38: 2.70E-15) e Table 177 (PDF 181: 2.71E-15)

## Eventos básicos

### STL_A: Falha de chave/transmissor de nivel do trem A

prob_missao = **8.1745E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | STL-FTOP-D | Beta | 0.500 | 6.132E+02 | 8.15E-04 | por demanda | 8.1500E-04 | PDF 36 (12) | Table 131, PDF 144 (A-85) |
| [ ] | STL-FTOP-R | Gamma | 0.500 | 4.916E+06 | 1.02E-07 | por hora | 2.4480E-06 | PDF 36 (12) | Table 131, PDF 144 (A-85) |

### STP_A: Falha de chave/transmissor de pressao do trem A

prob_missao = **1.3673E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | STP-FTOP-D | Beta | 0.500 | 4.278E+03 | 1.17E-04 | por demanda | 1.1700E-04 | PDF 36 (12) | Table 131, PDF 144 (A-85) |
| [ ] | STP-FTOP-R | Gamma | 0.500 | 6.083E+05 | 8.22E-07 | por hora | 1.9728E-05 | PDF 36 (12) | Table 131, PDF 144 (A-85) |

### STT_A: Falha de chave/transmissor de temperatura do trem A

prob_missao = **4.5215E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | STT-FTOP-D | Beta | 0.500 | 1.157E+03 | 4.32E-04 | por demanda | 4.3200E-04 | PDF 36 (12) | Table 131, PDF 144 (A-85) |
| [ ] | STT-FTOP-R | Gamma | 0.500 | 5.950E+05 | 8.40E-07 | por hora | 2.0160E-05 | PDF 36 (12) | Table 131, PDF 144 (A-85) |

### STF_A: Falha de chave/transmissor de vazao do trem A

prob_missao = **8.1745E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | STF-FTOP-D | Beta | 0.500 | 6.132E+02 | 8.15E-04 | por demanda | 8.1500E-04 | PDF 36 (12) | Table 131, PDF 144 (A-85) |
| [ ] | STF-FTOP-R | Gamma | 0.500 | 4.916E+06 | 1.02E-07 | por hora | 2.4480E-06 | PDF 36 (12) | Table 131, PDF 144 (A-85) |

### PIPE_A: Falha de tubulacao do trem A

prob_missao = **1.3385E-05**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | PIPE-OTHER-ELS | Gamma | 0.500 | 1.979E+09 | 2.53E-10 | por hora-pé | 1.2168E-05 | PDF 38 (14) | Table 177, PDF 181 (A-122) |
| [ ] | PIPE-OTHER-ELL ⚠️ conferir | Gamma | 0.300 | 1.187E+10 | 2.53E-11 | por hora-pé | 1.2168E-06 | PDF 38 (14) | Table 177, PDF 181 (A-122) |

### MOV_A: Falha de valvula motorizada do trem A

prob_missao = **6.4195E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | MOV-FTOC | Beta | 2.430 | 3.800E+03 | 6.40E-04 | por demanda | 6.4000E-04 | PDF 30 (6) | Table 14, PDF 65 (A-6) |
| [ ] | MOV-SOP-CCW | Gamma | 4.500 | 1.840E+08 | 2.45E-08 | por hora | 5.8800E-07 | PDF 30 (6) | Table 14, PDF 65 (A-6) |
| [ ] | MOV-ILS | Gamma | 0.451 | 1.250E+07 | 3.61E-08 | por hora | 8.6640E-07 | PDF 30 (6) | Table 14, PDF 65 (A-6) |
| [ ] | MOV-ILL | Gamma | 0.300 | 4.155E+08 | 7.22E-10 | por hora | 1.7328E-08 | PDF 30 (6) | Table 14, PDF 65 (A-6) |
| [ ] | MOV-ELS | Gamma | 0.463 | 2.460E+07 | 1.88E-08 | por hora | 4.5120E-07 | PDF 30 (6) | Table 14, PDF 65 (A-6) |
| [ ] | MOV-ELL | Gamma | 0.300 | 2.280E+08 | 1.32E-09 | por hora | 3.1680E-08 | PDF 30 (6) | Table 14, PDF 65 (A-6) |

### XVM_A: Falha de valvula manual do trem A

prob_missao = **5.2532E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | XVM-FTOC | Beta | 1.500 | 2.870E+03 | 5.22E-04 | por demanda | 5.2200E-04 | PDF 31 (7) | Table 38, PDF 82 (A-23) |
| [ ] | XVM-SOP | Gamma | 2.500 | 1.330E+08 | 1.88E-08 | por hora | 4.5120E-07 | PDF 31 (7) | Table 38, PDF 82 (A-23) |
| [ ] | XVM-ILS | Gamma | 3.500 | 1.330E+08 | 2.64E-08 | por hora | 6.3360E-07 | PDF 31 (7) | Table 38, PDF 82 (A-23) |
| [ ] | XVM-ILL | Gamma | 0.300 | 5.682E+08 | 5.28E-10 | por hora | 1.2672E-08 | PDF 31 (7) | Table 38, PDF 82 (A-23) |
| [ ] | XVM-ELS | Gamma | 11.500 | 1.330E+08 | 8.67E-08 | por hora | 2.0808E-06 | PDF 31 (7) | Table 38, PDF 82 (A-23) |
| [ ] | XVM-ELL | Gamma | 0.300 | 4.943E+07 | 6.07E-09 | por hora | 1.4568E-07 | PDF 31 (7) | Table 38, PDF 82 (A-23) |

### CKV_A: Falha de valvula de retencao do trem A

prob_missao = **1.3610E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | CKV-FTO | Beta | 0.500 | 4.480E+04 | 1.12E-05 | por demanda | 1.1200E-05 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-FTC | Beta | 5.500 | 4.480E+04 | 1.23E-04 | por demanda | 1.2300E-04 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-SOP | Gamma | 0.500 | 8.070E+08 | 6.20E-10 | por hora | 1.4880E-08 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-ILS | Gamma | 58.500 | 8.070E+08 | 7.25E-08 | por hora | 1.7400E-06 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-ILL | Gamma | 0.300 | 2.069E+08 | 1.45E-09 | por hora | 3.4800E-08 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-ELS | Gamma | 3.500 | 8.070E+08 | 4.34E-09 | por hora | 1.0416E-07 | PDF 31 (7) | Table 35, PDF 80 (A-21) |
| [ ] | CKV-ELL | Gamma | 0.300 | 9.875E+08 | 3.04E-10 | por hora | 7.2960E-09 | PDF 31 (7) | Table 35, PDF 80 (A-21) |

### FCV_A: Falha de valvula de controle de vazao do trem A

prob_missao = **4.7676E-05**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | FCV-FTOC | Beta | 0.500 | 1.130E+04 | 4.41E-05 | por demanda | 4.4100E-05 | PDF 31 (7) | Table 41, PDF 84 (A-25) |
| [ ] | FCV-FC | Gamma | 8.500 | 7.360E+07 | 1.15E-07 | por hora | 2.7600E-06 | PDF 31 (7) | Table 41, PDF 84 (A-25) |
| [ ] | FCV-SOP | Gamma | 2.500 | 7.360E+07 | 3.40E-08 | por hora | 8.1600E-07 | PDF 32 (8) | Table 41, PDF 84 (A-25) |

### HTX_A: Falha do trocador de calor do trem A

prob_missao = **1.9224E-05**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | HTX-PG-CCW | Gamma | 8.500 | 2.830E+07 | 3.01E-07 | por hora | 7.2240E-06 | PDF 38 (14) | Table 181, PDF 183 (A-124) |
| [ ] | HTX-ILS | Gamma | 61.500 | 2.230E+08 | 2.76E-07 | por hora | 6.6240E-06 | PDF 38 (14) | Table 181, PDF 183 (A-124) |
| [ ] | HTX-ILL | Gamma | 0.300 | 5.435E+07 | 5.52E-09 | por hora | 1.3248E-07 | PDF 38 (14) | Table 181, PDF 183 (A-124) |
| [ ] | HTX-ELS | Gamma | 0.825 | 4.350E+06 | 1.90E-07 | por hora | 4.5600E-06 | PDF 38 (14) | Table 181, PDF 183 (A-124) |
| [ ] | HTX-ELL | Gamma | 0.300 | 1.053E+07 | 2.85E-08 | por hora | 6.8400E-07 | PDF 38 (14) | Table 181, PDF 183 (A-124) |

### STL_B: Falha de chave/transmissor de nivel do trem B

Usa os mesmos dados de **STL_A**. prob_missao = **8.1745E-04**

### STP_B: Falha de chave/transmissor de pressao do trem B

Usa os mesmos dados de **STP_A**. prob_missao = **1.3673E-04**

### STT_B: Falha de chave/transmissor de temperatura do trem B

Usa os mesmos dados de **STT_A**. prob_missao = **4.5215E-04**

### STF_B: Falha de chave/transmissor de vazao do trem B

Usa os mesmos dados de **STF_A**. prob_missao = **8.1745E-04**

### PIPE_B: Falha de tubulacao do trem B

Usa os mesmos dados de **PIPE_A**. prob_missao = **1.3385E-05**

### MOV_B: Falha de valvula motorizada do trem B

Usa os mesmos dados de **MOV_A**. prob_missao = **6.4195E-04**

### XVM_B: Falha de valvula manual do trem B

Usa os mesmos dados de **XVM_A**. prob_missao = **5.2532E-04**

### CKV_B: Falha de valvula de retencao do trem B

Usa os mesmos dados de **CKV_A**. prob_missao = **1.3610E-04**

### FCV_B: Falha de valvula de controle de vazao do trem B

Usa os mesmos dados de **FCV_A**. prob_missao = **4.7676E-05**

### HTX_B: Falha do trocador de calor do trem B

Usa os mesmos dados de **HTX_A**. prob_missao = **1.9224E-05**

### MDP_A: Falha da bomba motriz A (trem A)

prob_missao = **5.0454E-04**  ·  fonte: INL/EXT-21-65055

| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | MDP-FTS-CCW ⚠️ conferir | Beta | 0.796 | 1.740E+03 | 4.57E-04 | conferir (Table 1 indica h) | 4.5700E-04 | PDF 32 (8) | Table 45, PDF 92 (A-33) |
| [ ] | MDP-FTR-CCW | Gamma | 1.850 | 1.040E+06 | 1.77E-06 | por hora | 4.2479E-05 | PDF 32 (8) | Table 45, PDF 92 (A-33) |
| [ ] | MDP-ELS | Gamma | 0.684 | 3.450E+06 | 1.98E-07 | por hora | 4.7520E-06 | PDF 32 (8) | Table 45, PDF 92 (A-33) |
| [ ] | MDP-ELL | Gamma | 0.300 | 2.165E+07 | 1.39E-08 | por hora | 3.3360E-07 | PDF 32 (8) | Table 45, PDF 92 (A-33) |

### MDP_C: Falha da bomba motriz C (trem A)

Usa os mesmos dados de **MDP_A**. prob_missao = **5.0454E-04**

### MDP_B: Falha da bomba motriz B (trem B)

Usa os mesmos dados de **MDP_A**. prob_missao = **5.0454E-04**

### MDP_D: Falha da bomba motriz D (trem B)

Usa os mesmos dados de **MDP_A**. prob_missao = **5.0454E-04**

## Fatores alfa (CCF), MDP, CCCG = 4

Fonte: INL/EXT-21-62940 Rev. 1. A ordem das colunas no PDF é **5th%, Mean, Median, 95th%**: a média vem **antes** da mediana.

| ok | Código | Modo | α1 | α2 | α3 | α4 | Soma | Página |
|---|---|---|---|---|---|---|---|---|
| [ ] | CCW-MDP-FS | FTS (Fail to Start) | 0.9854972 | 9.65E-03 | 3.08E-03 | 1.77E-03 | 1.00000 | Seção 2.1.11.1, CCCG = 4, p. 144 (PDF p. 164) |
| [ ] | CCW-MDP-FR | FTR (Fail to Run (Normally running equipment)) | 0.9860630 | 9.27E-03 | 2.96E-03 | 1.70E-03 | 0.99999 | Seção 2.1.11.2, CCCG = 4, p. 147 (PDF p. 167) |

Para conferir também: a tabela "ALPHA FACTOR and MGL PARAMETERS", coluna CCCG=4, na PDF 165 (FS) e na PDF 168 (FR). Nela os valores aparecem com 3 algarismos e batem com os de cima. Os dois modos têm **0 eventos de CCF** em 2006–2020, então os fatores refletem essencialmente a priori.

## Dados extraídos que não entraram na tabela final

- **Indisponibilidade por teste e manutenção** (Tables 2, 182 e 183: MDP-CCW, HTX-CCW, HDR-CCW e outras): a árvore não tem esses eventos. Os valores ficaram só em `extracao_bruta.csv`.
- **Versões genéricas substituídas pelas do CCW:** MOV-SOP, MDP-FTS-NS, MDP-FTS-NR, MDP-FTR<1H, MDP-FTR>1H, MDP-FTR-NR e HTX-LOHT. Também ficou de fora a alternativa HTX-PG-NE-CCW.
- **Modos não usados para evitar contar duas vezes:** MOV-FTO e MOV-FTC, já incluídos em MOV-FTOC.
- **Variantes que não se aplicam:** MOV-FC (válvula de controle de água de alimentação) e as válvulas borboleta (MOV-*-BFV), porque o tipo das MOVs do CCWS não está definido na árvore.

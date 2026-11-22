# Mapa dos relatórios-fonte

Gerado na Etapa 2 a partir dos sumários (lista de seções e de tabelas) dos dois PDFs.
Para confirmar as páginas, usei o cabeçalho e o rodapé de cada página e procurei a legenda
"Table N." no texto extraído com pypdf. **Os valores ainda não foram lidos**: isso fica para
a Etapa 3.

Convenção: **PDF** é a página física do arquivo, começando em 1, igual à usada nos nomes das
partes em `dados/brutos/partes/`. **Impressa** é o número que aparece na página.

---

## 1. AvgPara2020.pdf (INL/EXT-21-65055, 235 páginas)

### Conversão de numeração (verificada em todas as páginas)

| Trecho | Impressa | PDF |
|---|---|---|
| Pré-textual | i – xxii | 3 – 24 |
| Corpo (cap. 1–7) | n | n + 24 (1 → 25 … 35 → 59) |
| Apêndice A | A-n | n + 59 (A-1 → 60 … A-125 → 184) |
| Apêndice B | B-n | n + 184 (B-1 → 185 … B-8 → 192) |
| Apêndice C | C-n | n + 192 (C-1 → 193 … C-43 → 235) |

### Códigos dos componentes da árvore no relatório

Todos os 11 códigos de `modelo/arvore_falhas.yaml` aparecem no relatório com o mesmo nome,
inclusive `PIPE` (seção A-10.7, "PIPE (PIPE)"). Os sensores STF, STL, STP e STT ficam juntos
na seção A-7.3, "Sensor/Transmitter Components".

### 1.1 Tabelas-resumo no corpo do relatório

| Tabela | Conteúdo | Impressa | PDF | Parte | Observação |
|---|---|---|---|---|---|
| Table 1 | Component UR data and results (todos os componentes) | 6 – 14 | 30 – 38 | 1 | Começa na p. 29 (texto do cap. 2, impressa 5). Tem linhas específicas do CCW, como `MDP-FTS-CCW` (PDF 32) e `HTX-PG-CCW` (PDF 38). |
| Table 2 | Train UA data and results (indisponibilidade de trens por T&M) | 16 – 17 | 40 – 41 | 1 | Texto do cap. 3 a partir da p. 39. Tem `MDP-CCW` (PDF 40) e `HDR-CCW` (PDF 41). |

### 1.2 Fichas do Apêndice A (componentes da árvore)

Cada ficha traz a tabela de sistemas, a tabela de dados ("unreliability data") e a tabela
"Selected industry distributions of p and λ", que é a que tem distribuição, α, β, média, p05
e p95. As tabelas de modos de falha valem para uma família inteira de componentes.

| Código | Seção | Tabelas | Impressa | PDF | Parte |
|---|---|---|---|---|---|
| (válvulas) | A-1 | Table 8: Valve failure modes | A-1 | 60 | 1 |
| MOV | A-1.2 | 12 (sistemas), 13 (dados), 14 (distribuições) | A-4 – A-6 | 63 – 65 | 1 |
| CKV | A-1.9 | 33, 34, 35 | A-19 – A-21 | 78 – 80 | 1 |
| XVM | A-1.10 | 36, 37, 38 | A-22 – A-23 | 81 – 82 | 1 |
| FCV | A-1.11 | 39, 40, 41 | A-24 – A-25 | 83 – 84 | 1 |
| (bombas) | A-2 | Table 42: Pump failure modes | A-26 | 85 | 1 |
| MDP | A-2.1 | 43 (sistemas), 44 (dados, A-27 – A-30), 45 (distribuições) | A-26 – A-33 | 85 – 92 | 1 |
| (proteção do reator) | A-7 | Table 125: Reactor protection equipment failure modes | A-83 | 142 | 2 |
| STF, STL, STP, STT | A-7.3 | 130 (dados), 131 (distribuições) | A-85 | 144 | 2 |
| (diversos) | A-10 | Table 160: Failure modes applicable to miscellaneous equipment | A-107 | 166 | 2 |
| PIPE | A-10.7 | 175 (sistemas), 176 (dados), 177 (distribuições de λ) | A-121 – A-122 | 180 – 181 | 2 |
| HTX | A-10.8 | 178 (modos de falha), 179 (sistemas), 180 (dados), 181 (distribuições) | A-123 – A-124 | 182 – 183 | 2 |

Nas fichas de MOV, CKV, XVM, FCV, MDP, PIPE e HTX há linhas específicas do CCW. As páginas
com "CCW" no texto são 63–65, 78, 81, 83, 85–86, 92, 180–183. Na Etapa 3 vou conferir se essas
linhas existem também na tabela de distribuições, e não só nas de sistemas e de dados.

### 1.3 Tabelas de indisponibilidade por teste e manutenção (Apêndice B)

| Tabela | Conteúdo | Impressa | PDF | Parte | Observação |
|---|---|---|---|---|---|
| — | Introdução do Apêndice B | B-1 | 185 | 2 | |
| Table 182 | MSPI unavailability data and fitted distributions | B-2 – B-5 | 186 – 189 | 2 | Tem `HDR-CCW` (PDF 186), `HTX-CCW` (PDF 187) e `MDP-CCW` (PDF 188). |
| Table 183 | Other source unavailability estimates | B-6 – B-7 | 190 – 191 | 2 | |
| — | Referências | B-8 | 192 | 2 | Sem dados. |

### 1.4 Relevância por parte

| Parte | Relevante? | Páginas a ler (PDF) | Blocos de até 20 páginas |
|---|---|---|---|
| `AvgPara2020_p001-100.pdf` | **Sim** | 29–41; 60; 63–65; 78–92 | [29–41], [60, 63–65, 78–84], [85–92] |
| `AvgPara2020_p101-200.pdf` | **Sim** | 142; 144; 166; 180–183; 185–191 | [142, 144, 166, 180–183, 185–191] |
| `AvgPara2020_p201-235.pdf` | **Não, vou pular** | — | — |

**Por que pular a parte 3 (PDF 201–235):** ela só contém o restante do Apêndice C (C-9 a C-43),
com frequências de eventos iniciadores (LOCA, transientes, LOOP, perda de água de resfriamento
etc.). A árvore do CCWS não tem evento iniciador, apenas falhas de componentes. O Apêndice C
começa na PDF 193, que é parte 2, e também fica fora da leitura.

**Também não vou ler** nas partes 1 e 2:
- Tabelas 5 a 7 (PDF 49–55): comparam com a atualização de 2015 e não trazem parâmetros
  novos.
- Fichas de outros componentes (AOV, SOV, TDP, EDG etc.).
- Figuras de demandas por ano.

---

## 2. ccfparamest2020rev1.pdf (CCF Parameter Estimations 2020, Rev. 1, 481 páginas)

Este PDF é a fonte dos fatores alfa da Etapa 4, passo 3. Não existe planilha `.xlsx`.

### Conversão de numeração

Corpo: impressa n = PDF n + 20, verificado nas páginas 131–160 (PDF 151–180).

### Seções de MDP relevantes

| Seção | Modelo CCF | Impressa | PDF | Parte | Uso |
|---|---|---|---|---|---|
| Revision Notes | Mudanças da Rev. 1 (Tabelas R-1 a R-4) | xiii – xviii | 15 – 20 | 1 | Ler para saber quais templates foram revisados. A R-4 trata de inconsistências entre o relatório e a planilha original. |
| 2.1.11.1 | CCW-MDP-FS: CCW Motor-Driven Pumps Fail to Start | 144 – 146 | 164 – 166 | 2 | **Preferencial (CCW)** |
| 2.1.11.2 | CCW-MDP-FR: CCW Motor-Driven Pumps Fail to Run | 147 – 149 | 167 – 169 | 2 | **Preferencial (CCW)** |
| 2.1.1.1 | ALL-MDP-FS | 18 – 20 | 38 – 40 | 1 | Genérico (alternativa) |
| 2.1.1.2 | ALL-MDP-FH (fail to run < 1 h) | 21 – 23 | 41 – 43 | 1 | Genérico |
| 2.1.1.3 | ALL-MDP-FHRH (< 1 h e > 1 h) | 24 – 26 | 44 – 46 | 1 | Genérico |
| 2.1.1.4 | ALL-MDP-RH (> 1 h) | 27 – 29 | 47 – 49 | 1 | Genérico |
| 2.1.1.5 | ALL-MDP-NR-FR (normalmente em operação, fail to run) | 30 – 32 | 50 – 52 | 1 | Genérico |
| 2.1.1.6 | ALL-MDP-NS-FS (standby, fail to start) | 33 – 35 | 53 – 55 | 1 | Genérico |
| 2.1.1.7 | ALL-MDP-NR-FS (normalmente em operação, fail to start; revisado na Rev. 1) | 36 – 38 | 56 – 58 | 1 | Genérico |

Cada seção tem tabelas de α1…α8 com colunas por tamanho de grupo (CCCG = 2 … 8) e também
parâmetros de MGL. A coluna CCCG = 4 é a que interessa.

**Partes do CCF:** a parte 2 (101–200) é a principal e a parte 1 (1–100) serve como
alternativa genérica e para as notas de revisão. As partes 3, 4 e 5 (201–481) tratam de outros
componentes e dos apêndices e vou pulá-las, a menos que a Etapa 4 exija algo a mais.

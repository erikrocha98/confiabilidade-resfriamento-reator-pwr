# Progresso da extração (Etapa 3)

> **Ao retomar a sessão:** leia este arquivo primeiro e continue da **próxima parte pendente**.
> Não releia as partes já concluídas. As páginas de cada parte estão em `dados/mapa_relatorio.md`.

## Situação

| Parte | Status | Commit |
|---|---|---|
| `AvgPara2020_p001-100.pdf` (parte 1) | ✅ concluída | "Extração: parte 1" |
| `AvgPara2020_p101-200.pdf` (parte 2) | ✅ concluída | "Extração: parte 2" |
| `AvgPara2020_p201-235.pdf` (parte 3) | ⏭️ pulada (só eventos iniciadores, ver mapa) | — |
| `ccfparamest2020rev1_*` (fatores alfa) | ⏳ **próxima** (Etapa 4, passo 3) | — |

## Método

- O texto foi extraído com `pypdf`. As linhas foram reconhecidas por expressão regular e não
  digitadas à mão.
- Cada linha gravada em `extracao_bruta.csv` foi conferida automaticamente: a sequência
  "p05 mediana média p95 α β" precisa aparecer no texto da página de origem. Na parte 1 houve
  0 falhas.
- A mesma informação aparece em duas tabelas: a Table 1 do corpo e a tabela "Selected industry
  distributions" do Apêndice A. As duas foram registradas e comparadas. Na parte 1 houve
  **0 divergências** em distribuição, média, p05 e p95, e α e β diferem só por arredondamento
  (menos de 1%). A Table 1 tem α e β com mais casas decimais.
- A mediana, o fator de erro, o tipo de análise (EB/PL/KS ou JNID/IL) e o período estão na
  coluna `observacao`.

## Parte 1: PDF 1–100 (concluída)

**Páginas lidas** em 3 blocos:
- 29–41: Table 1 e Table 2.
- 60, 63–65, 78–84: Table 8 e as fichas de MOV, CKV, XVM e FCV.
- 85–92: Table 42 e a ficha de MDP.

**Encontrado: 102 linhas**

| Fonte | Linhas | Conteúdo |
|---|---|---|
| Table 1 (PDF 30–38) | 56 | MOV (15), CKV (7), XVM (6), FCV (3), MDP (9), STF/STL/STP/STT (8), PIPE (2), HTX (7) |
| Table 2 (PDF 40–41) | 7 | Teste e manutenção: MDP-ALL, MDP-CLEAN, MDP-NR-CLEAN, MDP-CCW, HTX (agrupado), HTX-CCW, HDR-CCW |
| Table 14 (PDF 65) | 14 | MOV |
| Table 35 (PDF 80) | 7 | CKV |
| Table 38 (PDF 82) | 6 | XVM |
| Table 41 (PDF 84) | 3 | FCV |
| Table 45 (PDF 92) | 9 | MDP |

**Versões específicas do CCW encontradas:** `MOV-SOP-CCW`, `MOV-BFV-SOP-CCW`, `MDP-FTS-CCW`,
`MDP-FTR-CCW`, `HTX-PG-CCW`, `HTX-PG-NE-CCW`, e as de teste e manutenção `MDP-CCW`, `HTX-CCW`
e `HDR-CCW`.

**Pontos de atenção:**
- `MDP-FTS-CCW` na Table 1 (PDF 32): a distribuição é Beta, ou seja, probabilidade por demanda,
  mas a coluna d/h mostra "h". As Tables 44 (PDF 86) e 45 (PDF 92) indicam demandas. A linha da
  Table 1 ficou marcada como **"conferir"**.
- As linhas STF-* foram estimadas com dados de STL (note d da Table 1). Por isso STF e STL têm
  valores idênticos.
- Os modos ELL e ILL não vêm de dados próprios: são derivados de ELS e ILS por multiplicadores do
  NUREG/CR-6928 (note c), com α = 0,3 assumido.
- Os p05 negativos da Table 2 são do ajuste Normal publicado no relatório e foram transcritos
  como estão.
- FCV só tem os modos FTOC, FC e SOP no relatório. Não há ELS, ILS, ELL nem ILL para FCV.
- PIPE é dado **por hora-pé**: a taxa vale por pé de tubulação. Para calcular a probabilidade na
  Etapa 4 vai ser preciso o comprimento da tubulação, que o relatório não fornece por sistema.
  O valor de "CCW footage" deve estar na Table 175 (PDF 180, parte 2).

**Linhas deixadas de fora de propósito:**
- Variantes de outros sistemas: SWS e CWS (`MOV-SOP-SWS`, `XVM-SOP-SWS`, `MDP-FTS/FTR-SWS`,
  `MDP-FTR-CWS`, `PIPE-SWS-*`) e FRV.
- Linhas de teste e manutenção de outros sistemas (AFW, ESW, RHR, HPI etc.).

## Parte 2: PDF 101–200 (concluída)

**Páginas lidas** em um bloco de 14 páginas: 142, 144, 166, 180–183 e 185–191.

**Encontrado: 22 linhas**

| Fonte | Linhas | Conteúdo |
|---|---|---|
| Table 131 (PDF 144) | 8 | STF, STL, STP, STT: FTOP por demanda (-D, Beta) e por hora (-R, Gamma) |
| Table 177 (PDF 181) | 2 | PIPE não-ESW (= PIPE-OTHER): ELS e ELL |
| Table 181 (PDF 183) | 7 | HTX: LOHT, ILS, ILL, ELS, ELL, PG-CCW, PG-NE-CCW |
| Table 182 (PDF 186–188) | 4 | Teste e manutenção pelo ajuste Normal: HDR-CCW, HTX-CCW, MDP-ALL, MDP-CCW |
| Table 183 (PDF 191) | 1 | HTX-TM (Beta, IPEs/SPAR), genérico sem p05 e p95 |

As Tables 125 (PDF 142) e 160 (PDF 166) só definem os modos de falha e não trazem valores.

**Cruzamento com o corpo do relatório:** todas as 21 linhas com par na Table 1 ou 2 batem, com
uma exceção:
- **`PIPE-OTHER-ELL` p05:** a Table 1 (PDF 38) dá 2.70E-15 e a Table 177 (PDF 181) dá 2.71E-15.
  As duas linhas ficaram marcadas como **"conferir"**.

**Pontos de atenção:**
- A Table 125 diz que FTOP é só "p", por demanda, mas a Table 131 e o texto da A-7.3.2 trazem as
  duas parcelas: por demanda e por tempo de calendário. As duas foram extraídas.
- Para PIPE, a Table 175 (PDF 180) informa que o CCW de uma PWR tem 4008 pés de tubulação por
  planta, com tubos de 2 polegadas ou mais (NUREG/CR-4407). A Table 176 registra 0,5 evento ELS
  em 3.321E+09 pé-hora no CCW, sem distribuição própria. Esses números foram anotados em
  `observacao`, sem cálculo.
- A Table 178 separa ELS em "tubo" e "casco" do HTX, mas a Table 181 traz um único ELS. Foi
  extraído como está.
- HTX-TM, da Table 183, não informa p05 nem p95.

**Deixados de fora:** as linhas ESW de PIPE e de teste e manutenção, que se referem a service
water, e os demais componentes das páginas lidas.

## Total da Etapa 3

**124 linhas** em `extracao_bruta.csv`: 102 da parte 1 e 22 da parte 2. A parte 3 foi pulada.

## Falta

- **Etapa 4, passo 3:** os fatores alfa do PDF do CCF. O preferido é a seção 2.1.11
  `CCW-MDP-FS`/`FR` (PDF 164–169, parte 2 do CCF). A alternativa genérica é 2.1.1 (PDF 38–58,
  parte 1 do CCF). As notas da Rev. 1 estão nas PDF 15–20.

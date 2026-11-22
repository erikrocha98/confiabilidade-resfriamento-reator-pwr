# Progresso da extração (Etapa 3)

> **Ao retomar a sessão:** leia este arquivo primeiro e continue da **próxima parte pendente**.
> Não releia as partes já concluídas. As páginas de cada parte estão em `dados/mapa_relatorio.md`.

## Situação

| Parte | Status | Commit |
|---|---|---|
| `AvgPara2020_p001-100.pdf` (parte 1) | ✅ concluída | "Extração: parte 1" |
| `AvgPara2020_p101-200.pdf` (parte 2) | ⏳ **próxima** | — |
| `AvgPara2020_p201-235.pdf` (parte 3) | ⏭️ pulada (só eventos iniciadores, ver mapa) | — |
| `ccfparamest2020rev1_*` (fatores alfa) | ⏳ Etapa 4, passo 3 | — |

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

## Falta

- **Parte 2 (PDF 101–200)**, em um bloco: 142 (Table 125), 144 (Tables 130 e 131, sensores),
  166 (Table 160), 180–183 (PIPE e HTX) e 185–191 (Apêndice B, Tables 182 e 183).
- **Etapa 4:** os fatores alfa do PDF do CCF (`CCW-MDP-FS`/`FR`, PDF 164–169).

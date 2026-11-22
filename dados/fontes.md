# Fontes dos dados

Todos os parametros de confiabilidade usados no trabalho vem dos dois relatorios
abaixo, que estao em `docs/` (PDFs nao versionados - ver `.gitignore`). As
colunas `fonte` e `pagina_tabela` dos CSVs apontam para estas entradas.

Os metadados abaixo foram conferidos na folha de rosto de cada PDF.

---

## `INL/EXT-21-65055`

- **Identificador do relatorio:** INL/EXT-21-65055
- **Titulo:** *Industry-Average Performance for Components and Initiating Events
  at U.S. Commercial Nuclear Power Plants: 2020 Update*
- **Autores:** Zhegang Ma; Thomas E. Wierman; Kellie J. Kvarfordt
- **Instituicao:** Idaho National Laboratory (INL), Idaho Falls, Idaho 83415, EUA
  (preparado para a Division of Risk Analysis, Office of Nuclear Regulatory
  Research, U.S. Nuclear Regulatory Commission; NRC Agreement 31310019N0006)
- **Data:** novembro de 2021
- **Arquivo neste repo:** `docs/AvgPara2020.pdf` (235 paginas)
- **Uso no trabalho:** taxas de falha e probabilidades por demanda dos eventos
  basicos independentes (MDP, MOV, XVM, CKV, FCV, HTX, PIPE, STL, STP, STT, STF).
- **Onde estao os numeros:**
  - *Table 1. Component UR data and results* (secao 2, corpo do relatorio) -
    tabela-resumo com todos os componentes e modos de falha. **E a fonte primaria
    da extracao.**
  - Apendice A (*Component Unreliability Data Sheets 2020 Update*) - fichas por
    componente, usadas para conferencia e para casos especificos.
- **Como citar nas celulas:** `fonte = INL/EXT-21-65055`,
  `pagina_tabela = Table 1, p. <n do relatorio> (PDF p. <n>)`

## `INL/EXT-21-62940 Rev. 1`

- **Identificador do relatorio:** INL/EXT-21-62940, Revision 1
- **Titulo:** *CCF Parameter Estimations, 2020 Update*
- **Autores:** Zhegang Ma; Kellie J. Kvarfordt
- **Instituicao:** Idaho National Laboratory (INL), Idaho Falls, Idaho 83415, EUA
  (preparado para a U.S. Nuclear Regulatory Commission)
- **Data:** agosto de 2022 (Revisao 1)
- **Arquivo neste repo:** `docs/ccfparamest2020rev1.pdf` (481 paginas)
- **Uso no trabalho:** fatores alfa de falha de causa comum (CCF) dos grupos
  redundantes, em `fatores_alfa_ccf.csv`.
- **Como citar nas celulas:** `fonte = INL/EXT-21-62940-R1`,
  `pagina_tabela = <tabela>, p. <n do relatorio> (PDF p. <n>)`
- **Observacao:** existe uma planilha `.xlsx` companheira deste relatorio com os
  mesmos fatores alfa. Ela nao esta em `docs/`; a extracao foi feita do PDF. Se a
  planilha for adicionada ao repo, vale reconferir os valores por ela.

---

## Rastreabilidade da extracao

A extracao e feita por script, em duas etapas, para que qualquer valor possa ser
reconferido no PDF:

1. `python scripts/extrair_dados_inl.py` le os PDFs e gera
   `dados/extracao_bruta.csv`, com **a pagina de origem de cada linha** e o texto
   da linha como lido do PDF.
2. `python scripts/montar_parametros.py` seleciona do arquivo bruto as linhas dos
   24 eventos basicos da arvore e gera `dados/parametros_eventos.csv`.

Nenhum valor e digitado a mao e nenhum valor e inventado: tudo vem do texto dos
PDFs, com pagina registrada.

## Outras referencias do relatorio final

Referencias de metodologia (arvore de falhas, cortes minimos, medidas de
importancia, Monte Carlo) usadas no texto do trabalho, nao nos dados:

- [conferir] Livro-texto / notas de aula da disciplina de Confiabilidade de Sistemas (UFMG).
- [conferir] Outras referencias citadas pelas frentes 3, 4 e 5.

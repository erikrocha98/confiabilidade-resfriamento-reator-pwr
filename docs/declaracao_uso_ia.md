# Declaracao de uso de Inteligencia Artificial

Registro do uso de ferramentas de IA no trabalho de Confiabilidade de Sistemas
(UFMG) - estudo de confiabilidade do CCWS.

**Cada integrante preenche uma linha por uso.** Atualizar este arquivo no mesmo
pull request em que o trabalho assistido por IA entra no repositorio.

## Principios adotados pelo grupo

1. **Dados nunca sao inventados.** Taxas de falha, probabilidades, fatores alfa e
   qualquer outro valor numerico vem dos relatorios do INL, com `fonte` e
   `pagina_tabela` registrados (ver `dados/fontes.md`). A extracao foi feita com
   IA usando scripts Python (uso #2) e conferida manualmente via
   `dados/conferencia.md`.
2. **Responsabilidade e humana.** Todo texto, codigo ou resultado gerado com
   auxilio de IA foi lido, conferido e, quando necessario, corrigido pelo
   integrante responsavel, que responde por ele.
3. **Transparencia.** Usos relevantes de IA estao registrados na tabela abaixo.

## Registro de usos

| # | Data | Quem usou | Ferramenta (e versao/modelo) | Finalidade | Etapa / frente | Arquivos afetados | Conferencia feita |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-11-21 | [nome] | Claude Code (Anthropic, modelo Opus) | Geracao do esqueleto do repositorio: estrutura de pastas, READMEs, cabecalhos dos CSVs, codigo compartilhado (`ccws/arvore.py`, `ccws/dados.py`), script de validacao e testes. Nenhum valor numerico de confiabilidade foi gerado. | Preparacao / infraestrutura (todas as frentes) | estrutura inicial do repositorio (commit "Esqueleto inicial do projeto") | [preencher: quem revisou o codigo e os testes] |
| 2 | 2026-11-21 | [nome] | Claude Code (Anthropic, modelo Opus 5.5) | Divisao dos PDFs do INL em partes de 100 paginas e **extracao dos parametros de confiabilidade com IA, usando scripts Python (pypdf + expressoes regulares)**: taxas/probabilidades e distribuicoes do INL/EXT-21-65055 (Tables 1, 2, 14, 35, 38, 41, 45, 131, 177, 181, 182, 183) e fatores alfa do INL/EXT-21-62940 Rev. 1 (secao 2.1.11, CCCG = 4). Montagem de `parametros_eventos.csv` e calculo de `prob_missao`. Nenhum valor foi estimado: celulas sem dado ficaram vazias com "nao encontrado". | Frente 2 (dados) | `scripts/dividir_pdf.py`, `scripts/montar_parametros.py`, `scripts/extracao/`, `dados/mapa_relatorio.md`, `dados/extracao_bruta.csv`, `dados/progresso_extracao.md`, `dados/parametros_eventos.csv`, `dados/fatores_alfa_ccf.csv`, `dados/conferencia.md`, `dados/README.md` (secao de suposicoes) | Automatica: cada valor extraido foi procurado de volta no texto da pagina de origem (0 falhas) e cruzado entre a Table 1 e o Apendice A (1 divergencia, marcada "conferir"); fatores alfa cruzados com a tabela-resumo de cada secao. **Manual: [preencher - quem conferiu `dados/conferencia.md` contra os PDFs]** |
| 3 | 2026-11-22 | Caue | Antigravity (Google DeepMind) | Planejamento do roadmap da Frente 4 da implementacao da simulacao de Monte Carlo (modelo base em redundancia ativa, avaliacao vetorizada em lotes, ICs de Wald/Wilson/Clopper-Pearson, curva de convergencia, dimensionamento de N, grafico, extensao dinamica de bomba em espera e motor DES de reparo parametrizado, e testes unitarios). Nenhum valor numerico de confiabilidade ou MTTR foi gerado ou inventado. | Frente 4 (Monte Carlo) | `monte_carlo/simulacao.py`, `monte_carlo/convergencia.py`, `monte_carlo/dinamico.py`, `monte_carlo/README.md`, `tests/test_monte_carlo.py`, `docs/declaracao_uso_ia.md` | Conferencia contra `ccws.arvore.avalia`, consistencia entre `extracao_bruta.csv` e `parametros_eventos.csv`, e validacao de saidas; revisao humana manual de todas as implementações. |
| 4 | | | | | | | |

## Como preencher

- **Ferramenta:** nome e, se souber, o modelo/versao (ex.: "Claude Code - Opus",
  "ChatGPT - GPT-5", "GitHub Copilot").
- **Finalidade:** o que foi pedido a ferramenta, de forma concreta
  (ex.: "revisar a implementacao dos cortes minimos", "melhorar a redacao da
  secao de metodologia").
- **Etapa / frente:** frente de trabalho (1 a 5) ou etapa (redacao do relatorio,
  revisao, infraestrutura).
- **Conferencia feita:** como o resultado foi verificado (ex.: "testes do pytest
  passando", "resultado conferido a mao em um exemplo", "comparado com o
  livro-texto").

## O que NAO foi feito com IA

- Escolha de valores: nenhum parametro foi estimado ou completado pela IA; ela
  apenas transcreveu valores das tabelas do INL (ver uso #2).
- [completar conforme o trabalho avanca: definicao da arvore de falhas, escolha
  dos cenarios de sensibilidade, conclusoes do relatorio, etc.]

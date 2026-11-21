# Declaracao de uso de Inteligencia Artificial

Registro do uso de ferramentas de IA no trabalho de Confiabilidade de Sistemas
(UFMG) - estudo de confiabilidade do CCWS.

**Cada integrante preenche uma linha por uso.** Atualizar este arquivo no mesmo
pull request em que o trabalho assistido por IA entra no repositorio.

## Principios adotados pelo grupo

1. **Dados nunca vem de IA.** Taxas de falha, probabilidades, fatores alfa e
   qualquer outro valor numerico sao extraidos manualmente dos relatorios do
   INL, com `fonte` e `pagina_tabela` registrados. Ver `dados/fontes.md`.
2. **Responsabilidade e humana.** Todo texto, codigo ou resultado gerado com
   auxilio de IA foi lido, conferido e, quando necessario, corrigido pelo
   integrante responsavel, que responde por ele.
3. **Transparencia.** Usos relevantes de IA estao registrados na tabela abaixo.

## Registro de usos

| # | Data | Quem usou | Ferramenta (e versao/modelo) | Finalidade | Etapa / frente | Arquivos afetados | Conferencia feita |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-11-21 | [nome] | Claude Code (Anthropic, modelo Opus) | Geracao do esqueleto do repositorio: estrutura de pastas, READMEs, cabecalhos dos CSVs, codigo compartilhado (`ccws/arvore.py`, `ccws/dados.py`), script de validacao e testes. Nenhum valor numerico de confiabilidade foi gerado. | Preparacao / infraestrutura (todas as frentes) | estrutura inicial do repositorio (commit "Esqueleto inicial do projeto") | [preencher: quem revisou o codigo e os testes] |
| 2 | | | | | | | |
| 3 | | | | | | | |

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

- Extracao dos parametros dos relatorios do INL (`dados/parametros_eventos.csv`,
  `dados/fatores_alfa_ccf.csv`): feita manualmente, com conferencia pagina por pagina.
- [completar conforme o trabalho avanca: definicao da arvore de falhas, escolha
  dos cenarios de sensibilidade, conclusoes do relatorio, etc.]

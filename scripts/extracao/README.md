# Scripts de extração (frente 2)

Scripts usados na extração com IA dos relatórios do INL (ver `docs/declaracao_uso_ia.md`, uso #2).
Ficam aqui para que a extração possa ser **reproduzida e auditada**. As páginas lidas por cada
script estão em `dados/mapa_relatorio.md`.

Para reproduzir `dados/extracao_bruta.csv` do zero, rode da raiz do repositório, nesta ordem:

```bash
CAB="parte,pagina_pdf,pagina_impressa,tabela,componente,modo_falha,distribuicao,param_alfa,param_beta,media,p05,p95,unidade,observacao"
echo "$CAB" > dados/extracao_bruta.csv
.venv/bin/python scripts/extracao/parse_t1t2.py 1 docs/AvgPara2020.pdf dados/extracao_bruta.csv      # Tables 1 e 2
.venv/bin/python scripts/extracao/parse_apA.py 1 docs/AvgPara2020.pdf dados/extracao_bruta.csv \
    "65:Table 14:MOV" "80:Table 35:CKV" "82:Table 38:XVM" "84:Table 41:FCV" "92:Table 45:MDP"      # Apêndice A, parte 1
.venv/bin/python scripts/extracao/parse_p2.py docs/AvgPara2020.pdf dados/extracao_bruta.csv          # Apêndices A e B, parte 2
head -1 dados/fatores_alfa_ccf.csv > /tmp/cab && cp /tmp/cab dados/fatores_alfa_ccf.csv
.venv/bin/python scripts/extracao/parse_ccf.py docs/ccfparamest2020rev1.pdf dados/extracao_bruta.csv dados/fatores_alfa_ccf.csv
.venv/bin/python scripts/montar_parametros.py                                                         # parametros_eventos.csv
.venv/bin/python scripts/extracao/gerar_conferencia.py .                                              # conferencia.md
```

As anotações "conferir" que foram acrescentadas à mão no `extracao_bruta.csv`
(`MDP-FTS-CCW` da Table 1, `PIPE-OTHER-ELL`) não são geradas por esses scripts: depois de
reproduzir a extração, refaça-as ou compare com a versão do repositório.

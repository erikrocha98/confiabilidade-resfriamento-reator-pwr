import csv, sys, math
from pathlib import Path
RAIZ = Path(sys.argv[1]); sys.path.insert(0, str(RAIZ / 'scripts')); sys.path.insert(0, str(RAIZ))
import montar_parametros as mp
from ccws import dados as md, arvore as ma
t = float(md.carregar_config()['tempo_missao_h'])
bruta = list(csv.DictReader(open(RAIZ / 'dados/extracao_bruta.csv')))
t1 = {r['modo_falha']: r for r in bruta if r['tabela'] == 'Table 1'}
apx = {r['modo_falha']: r for r in bruta if r['tabela'] not in ('Table 1', 'Table 2') and r['parte'] in ('1', '2')}
par = {r['id_evento']: r for r in csv.DictReader(open(RAIZ / 'dados/parametros_eventos.csv'))}
alfa = list(csv.DictReader(open(RAIZ / 'dados/fatores_alfa_ccf.csv')))
arv = ma.carregar_arvore()
o = []
o.append('# Conferência manual dos dados extraídos\n')
o.append('Este arquivo lista, para cada evento da árvore, o valor de cada modo de falha e a página de onde ele saiu. '
         'Serve para conferir à mão contra os PDFs em `docs/`.\n')
o.append('- **Como foi gerado:** os valores foram extraídos com IA (Claude Code), usando scripts Python com pypdf; '
         'veja `docs/declaracao_uso_ia.md`. Por isso **cada linha precisa ser conferida por um integrante**: '
         'marque `[x]` depois de conferir.')
o.append('- **Páginas:** "PDF" é a página física do arquivo e "impressa" é o número que aparece na página '
         '(ver `dados/mapa_relatorio.md`).')
o.append('- **Fonte dos valores:** a Table 1 do INL/EXT-21-65055. A coluna "Conferir também" aponta a mesma linha no '
         'Apêndice A, que deve bater. A Table 1 tem α e β com mais casas decimais.')
o.append(f'- **Cálculo:** P_i = média, para falha sob demanda (Beta); P_i = 1 − exp(−λ·t), para taxa (Gamma), com t = {t:g} h. '
         'A probabilidade do evento é prob_missao = 1 − ∏(1 − P_i).')
o.append(f'- **Suposição para PIPE:** λ é por hora-pé, e o comprimento usado foi {mp.PES_CCW_PLANTA} ft ÷ 2 trens = '
         f'{mp.PES_POR_TREM:g} ft por trem (ver `dados/README.md`).\n')
o.append('## Itens marcados "conferir"\n')
for r in bruta:
    if 'conferir' in r['observacao']:
        o.append(f"- [ ] **{r['modo_falha']}**, {r['tabela']} (PDF {r['pagina_pdf']}, impressa {r['pagina_impressa']}): "
                 + r['observacao'].split('conferir:')[-1].strip())
o.append('')
o.append('## Eventos básicos\n')
feitos = {}
for ev in arv.lista_eventos_basicos():
    info = arv.info_eventos_basicos[ev]; comp = info['componente']; p = par[ev]
    if comp in feitos:
        o.append(f"### {ev}: {arv.descricao(ev)}\n\nUsa os mesmos dados de **{feitos[comp]}**. "
                 f"prob_missao = **{p['prob_missao']}**\n")
        continue
    feitos[comp] = ev
    o.append(f"### {ev}: {arv.descricao(ev)}\n")
    o.append(f"prob_missao = **{p['prob_missao']}**  ·  fonte: {p['fonte']}\n")
    o.append('| ok | Código INL | Distrib. | α | β | Média | Unid. | P_i (t) | Table 1: PDF (impressa) | Conferir também |')
    o.append('|---|---|---|---|---|---|---|---|---|---|')
    for cod in p['codigo_inl'].split('; '):
        r = t1[cod]; pi, _ = mp.prob_modo(r, t); a = apx.get(cod)
        extra = f"{a['tabela']}, PDF {a['pagina_pdf']} ({a['pagina_impressa']})" if a else '—'
        flag = ' ⚠️ conferir' if 'conferir' in r['observacao'] else ''
        o.append(f"| [ ] | {cod}{flag} | {r['distribuicao']} | {r['param_alfa']} | {r['param_beta']} | {r['media']} | "
                 f"{r['unidade']} | {pi:.4E} | PDF {r['pagina_pdf']} ({r['pagina_impressa']}) | {extra} |")
    o.append('')
o.append('## Fatores alfa (CCF), MDP, CCCG = 4\n')
o.append('Fonte: INL/EXT-21-62940 Rev. 1. A ordem das colunas no PDF é **5th%, Mean, Median, 95th%**: '
         'a média vem **antes** da mediana.\n')
o.append('| ok | Código | Modo | α1 | α2 | α3 | α4 | Soma | Página |')
o.append('|---|---|---|---|---|---|---|---|---|')
for a in alfa:
    s = sum(float(a[f'alfa_{k}']) for k in '1234')
    o.append(f"| [ ] | {a['codigo_inl']} | {a['modo_falha']} | {a['alfa_1']} | {a['alfa_2']} | {a['alfa_3']} | {a['alfa_4']} | {s:.5f} | {a['pagina_tabela']} |")
o.append('\nPara conferir também: a tabela "ALPHA FACTOR and MGL PARAMETERS", coluna CCCG=4, na PDF 165 (FS) e na PDF 168 (FR). '
         'Nela os valores aparecem com 3 algarismos e batem com os de cima. Os dois modos têm **0 eventos de CCF** '
         'em 2006–2020, então os fatores refletem essencialmente a priori.\n')
o.append('## Dados extraídos que não entraram na tabela final\n')
o.append('- **Indisponibilidade por teste e manutenção** (Tables 2, 182 e 183: MDP-CCW, HTX-CCW, HDR-CCW e outras): '
         'a árvore não tem esses eventos. Os valores ficaram só em `extracao_bruta.csv`.')
o.append('- **Versões genéricas substituídas pelas do CCW:** MOV-SOP, MDP-FTS-NS, MDP-FTS-NR, MDP-FTR<1H, MDP-FTR>1H, '
         'MDP-FTR-NR e HTX-LOHT. Também ficou de fora a alternativa HTX-PG-NE-CCW.')
o.append('- **Modos não usados para evitar contar duas vezes:** MOV-FTO e MOV-FTC, já incluídos em MOV-FTOC.')
o.append('- **Variantes que não se aplicam:** MOV-FC (válvula de controle de água de alimentação) e as válvulas borboleta '
         '(MOV-*-BFV), porque o tipo das MOVs do CCWS não está definido na árvore.')
open(RAIZ / 'dados/conferencia.md', 'w').write('\n'.join(o) + '\n')
print('ok', len(o), 'linhas')

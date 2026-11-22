"""Extrai fatores alfa CCCG=4 das secoes CCW-MDP do relatorio de CCF (INL/EXT-21-62940 Rev. 1)."""
import re, sys, csv
from pypdf import PdfReader
PDF, BRUTA, ALFA = sys.argv[1:4]
r = PdfReader(PDF)
NUM = r'\d\.\d+(?:E[+-]\d+)?'
SECOES = [(164, '2.1.11.1', 'CCW-MDP-FS', 'Fail to Start', 'FTS'), (167, '2.1.11.2', 'CCW-MDP-FR', 'Fail to Run (Normally running equipment)', 'FTR')]
bruta, alfa = [], []
for pdf_p, sec, cod, modo, curto in SECOES:
    ls = [l.strip() for l in r.pages[pdf_p - 1].extract_text().splitlines()]
    texto = ' '.join(ls)
    assert cod in texto and modo in texto, (cod, modo)
    ind = re.search(r'Independent Failure Events: ([\d.]+)', texto).group(1)
    nccf = re.search(r'Common-Cause Failure Events: ([\d.]+)', texto).group(1)
    i0 = ls.index('CCCG = 4')
    assert ls[i0 + 3].startswith('5th% Mean Median 95th% MLE a b'), ls[i0 + 1:i0 + 4]
    vals = {}
    for l in ls[i0 + 4:i0 + 8]:
        m = re.match(rf'^α([1-4]) ({NUM}) ({NUM}) ({NUM}) ({NUM}) ({NUM}) ({NUM}) ({NUM})$', l)
        k, p05, mean, med, p95, mle, a, b = m.groups()
        vals[k] = mean
        bruta.append(['CCF parte 2', pdf_p, str(pdf_p - 20), f'{sec} ALPHA FACTOR DISTRIBUTIONS, CCCG = 4', 'MDP',
                      f'{cod} α{k} (CCCG=4)', 'Beta', a, b, mean, p05, p95, 'adimensional',
                      f'fonte INL/EXT-21-62940-R1; ordem das colunas no PDF: 5th% Mean Median 95th% MLE a b; '
                      f'mediana={med}; MLE={mle}; eventos independentes={ind}; eventos CCF={nccf}'])
    soma = sum(float(vals[k]) for k in '1234')
    obs = (f'médias da tabela "ALPHA FACTOR DISTRIBUTIONS", CCCG = 4 (distribuições Beta com a e b em extracao_bruta.csv); '
           f'soma α1..α4 = {soma:.7f}; {ind} eventos independentes e {nccf} eventos CCF (2006–2020): fatores dominados pela priori; '
           'relatório não distingue teste escalonado/não escalonado (não encontrado); versão específica CCW preferida à genérica ALL-MDP (seção 2.1.1); '
           'seção não alterada na Rev. 1 (Tabela R-1)')
    alfa.append(['MDP', cod, curto + f' ({modo})', 4, vals['1'], vals['2'], vals['3'], vals['4'], '',
                 'INL/EXT-21-62940-R1', f'Seção {sec}, CCCG = 4, p. {pdf_p - 20} (PDF p. {pdf_p})', obs])
with open(BRUTA, 'a', newline='') as f: csv.writer(f).writerows(bruta)
with open(ALFA, 'a', newline='') as f: csv.writer(f).writerows(alfa)
for x in alfa: print(x[:9])

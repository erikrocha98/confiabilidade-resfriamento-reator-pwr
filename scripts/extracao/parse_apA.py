"""Extrai tabelas 'Selected industry distributions of p and λ' do Apêndice A."""
import re, sys, csv
from pypdf import PdfReader
PART, PDF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TABELAS = [(int(x.split(':')[0]), x.split(':')[1], x.split(':')[2]) for x in sys.argv[4:]]  # pdf:Table N:COMP
r = PdfReader(PDF)
NUM = r'\d\.\d+E[+-]\d+'
row_re = re.compile(rf'^(\S+)\s+(\S+)\s+(\S+)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+(Beta|Gamma|Lognormal)\s+([\d.]+)\s+({NUM})\s*$')
UNID = {'Beta': 'por demanda', 'Gamma': 'por hora'}
SUF_MDP = {('STBY', 'FTS'): 'FTS-NS', ('NR', 'FTS'): 'FTS-NR', ('NR', 'FTR'): 'FTR-NR'}
rows = []
for pdf_p, tab, comp in TABELAS:
    lines = r.pages[pdf_p - 1].extract_text().splitlines()
    ini = next(i for i, l in enumerate(lines) if l.strip().startswith(f'{tab}. Selected'))
    for l in lines[ini + 1:]:
        m = row_re.match(l.strip())
        if not m:
            if rows and l.strip() == '': break
            continue
        g, mode, an, p05, med, mean, p95, dist, a, b = m.groups()
        if g in ('SWS', 'CWS', 'FRV'): continue
        if comp == 'MDP' and (g, mode) in SUF_MDP: code = f'MDP-{SUF_MDP[(g, mode)]}'
        elif g in ('--', '-', '—', comp, 'STBY'): code = f'{comp}-{mode}'
        elif g == 'BFV': code = f'{comp}-{mode}-BFV'
        elif g == 'BFV--CCW': code = f'{comp}-BFV-{mode}-CCW'
        else: code = f'{comp}-{mode}-{g}'
        obs = f'{tab} (Apêndice A); grupo={g}; analise={an}; mediana={med}; α e β arredondados na tabela'
        if mode in ('ELL', 'ILL'): obs += '; ELL/ILL derivado de ELS/ILS (multiplicador NUREG/CR-6928, α=0,3 assumido)'
        if code == 'MDP-FTS-CCW': obs += '; Table 44 (PDF 86) indica 80,067 d (demandas), o que confirma a unidade por demanda'
        rows.append([PART, pdf_p, f'A-{pdf_p - 59}', tab, comp, code, dist, a, b, mean, p05, p95, UNID[dist], obs])
with open(OUT, 'a', newline='') as f: csv.writer(f).writerows(rows)
for x in rows: print(x[1], x[3], x[5], x[6], x[7], x[8], x[9], x[10], x[11])
print(len(rows), 'linhas')

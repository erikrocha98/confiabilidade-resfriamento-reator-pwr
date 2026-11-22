import re, sys, csv
from pypdf import PdfReader
PDF, OUT = sys.argv[1], sys.argv[2]
r = PdfReader(PDF)
NUM = r'-?\d\.\d+E[+-]\d+'
def L(p): return [l.strip() for l in r.pages[p - 1].extract_text().splitlines()]
rows = []
def add(p, lab, tab, comp, code, dist, a, b, mean, p05, p95, unid, obs):
    rows.append(['2', p, lab, tab, comp, code, dist, a, b, mean, p05, p95, unid, obs])
# --- Table 131 (PDF 144): sensores
rx = re.compile(rf'^(?:All\s+)?(STF|STL|STP|STT)\s+FTOP\s+(STL|RPS SS)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+(Beta|Gamma)\s+([\d.]+)\s+({NUM})$')
for s in L(144):
    m = rx.match(s)
    if not m: continue
    c, fonte, p05, med, mean, p95, dist, a, b = m.groups()
    suf = 'D' if dist == 'Beta' else 'R'
    obs = f'Table 131 (Apêndice A); fonte={fonte}; mediana={med}; α=0,5 assumido (dados RPS SS 1984–1995)'
    if c == 'STF': obs += '; STF sem dados próprios, usa resultado de STL (texto A-7.3.3)'
    add(144, 'A-85', 'Table 131', c, f'{c}-FTOP-{suf}', dist, a, b, mean, p05, p95,
        'por demanda' if dist == 'Beta' else 'por hora', obs)
# --- Table 177 (PDF 181): PIPE
ls = L(181); i0 = next(i for i, s in enumerate(ls) if s.startswith('Table 177.'))
sistema = None
rx = re.compile(rf'^(ESW|Non-ESW)?\s*(ELS|ELL)\s+(\S+)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+(Gamma)\s+([\d.]+)\s+({NUM})$')
for s in ls[i0:]:
    m = rx.match(s)
    if not m: continue
    sis, mode, an, p05, med, mean, p95, dist, a, b = m.groups()
    sistema = sis or sistema
    if sistema != 'Non-ESW': continue  # ESW = service water, não se aplica ao CCW
    obs = (f'Table 177 (Apêndice A); sistema=Non-ESW (equivale a PIPE-OTHER da Table 1); analise={an}; mediana={med}; '
           'taxa por hora-pé; Table 175 (PDF 180): CCW PWR = 4008 pés por planta (NUREG/CR-4407, tubos ≥ 2 pol.)')
    if mode == 'ELS': obs += '; Table 1 dá β=1.979E+09 e análise JNID/IL, esta tabela dá 1.978E+09 e SCNID/IL (arredondamento/rótulo); Table 176: CCW teve 0,5 evento ELS em 3.321E+09 pé-h (1997–2004), sem distribuição própria'
    else: obs += '; ELL = ELS × 0,1 para tubulação não-ESW, α=0,3 assumido'
    add(181, 'A-122', 'Table 177', 'PIPE', f'PIPE-OTHER-{mode}', dist, a, b, mean, p05, p95, 'por hora-pé', obs)
# --- Table 181 (PDF 183): HTX
ls = L(183); i0 = next(i for i, s in enumerate(ls) if s.startswith('Table 181.'))
rx = re.compile(rf'^(--|CCW|CCW-NE)\s+(\S+)\s+(\S+)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+(Gamma|Beta)\s+([\d.]+)\s+({NUM})$')
for s in ls[i0:]:
    m = rx.match(s)
    if not m: continue
    g, mode, an, p05, med, mean, p95, dist, a, b = m.groups()
    code = {'--': f'HTX-{mode}', 'CCW': 'HTX-PG-CCW', 'CCW-NE': 'HTX-PG-NE-CCW'}[g]
    obs = f'Table 181 (Apêndice A); grupo={g}; analise={an}; mediana={med}; α e β arredondados na tabela'
    if mode in ('ELL', 'ILL'): obs += '; ELL/ILL derivado (multiplicador NUREG/CR-6928, α=0,3 assumido)'
    if g == 'CCW': obs += '; PG = plugging (entupimento) em HTX do CCW, normalmente em operação'
    if g == 'CCW-NE': obs += '; PG não-ExEE (Table 1: "Plugging Non-ExEE")'
    add(183, 'A-124', 'Table 181', 'HTX', code, dist, a, b, mean, p05, p95, 'por hora', obs)
# --- Table 182 (PDF 186-189): T&M MSPI, distribuição Normal ajustada
for p in range(186, 190):
    ls = L(p)
    for i, s in enumerate(ls):
        m = re.match(r'^(MDP-ALL|MDP-CCW|HTX-CCW|HDR-CCW) \((\d+) Trains, (\S+)\)$', s)
        if not m: continue
        code, ntr, per = m.groups(); v = {}
        for t in ls[i + 1:i + 9]:
            mm = re.match(rf'^(Mean|SD|95%|Median|5%|EF)\s+({NUM}|[\d.]+)\s+({NUM}|[\d.]+)$', t)
            if mm: v[mm.group(1)] = mm.group(3)   # coluna "Normal Distribution"
        obs = (f'Table 182 (Apêndice B), coluna "Normal Distribution"; {ntr} trens; periodo={per}; '
               f'mediana={v["Median"]}; desvio_padrao={v["SD"]}; EF={v["EF"]}')
        if v['5%'].startswith('-'): obs += '; p05 negativo no ajuste Normal, transcrito como está'
        if code == 'HDR-CCW': obs += '; header do CCW, sem evento correspondente na árvore'
        add(p, f'B-{p - 184}', 'Table 182', code.split('-')[0], f'{code} (T&M)', 'Normal', '', '',
            v['Mean'], v['5%'], v['95%'], 'probabilidade (indisponibilidade)', obs)
# --- Table 183 (PDF 191): HTX-TM
for s in L(191):
    m = re.match(rf'^HTX-TM .* (Beta) ({NUM}) ([\d.]+) ([\d.]+) ([\d.]+)$', s)
    if m:
        dist, mean, a, b, ef = m.groups()
        add(191, 'B-7', 'Table 183', 'HTX', 'HTX-TM (T&M)', dist, a, b, mean, '', '', 'probabilidade (indisponibilidade)',
            f'Table 183 (Apêndice B); fonte IPEs/SPAR; EF={ef}; p05 e p95 não informados na tabela (não encontrado)')
with open(OUT, 'a', newline='') as f: csv.writer(f).writerows(rows)
for x in rows: print(x[1], x[3], x[5], x[6], x[7], x[8], x[9], x[10], x[11])
print(len(rows), 'linhas')

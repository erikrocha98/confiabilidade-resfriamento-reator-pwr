import re, sys, csv
from pypdf import PdfReader
PART = sys.argv[1]; PDF = sys.argv[2]; OUT = sys.argv[3]
r = PdfReader(PDF)
COMP = r'(MOV|CKV|XVM|FCV|MDP|HTX|STF|STL|STP|STT|PIPE)'
NUM = r'-?\d\.\d+E[+-]\d+'
end1 = re.compile(rf'\s(d|h|h-ft)\s+(\d+|--)\s+(Beta|Gamma|Lognormal|Normal)\s+(\S+)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+([\d.]+|--)\s+({NUM}|--)\s+([\d.]+|--)\s+(\S+)\s*$')
end2 = re.compile(rf'(EPIX/RADS|IPEs|Letter|Unknown|RPS SS|Existing SPAR)\s+(\S+)\s+(\d+|--)\s+(Beta|Normal|Lognormal)\s+({NUM}|--)\s+({NUM}|--)\s+({NUM})\s+({NUM}|--)\s+([\d.]+|--)\s+([\d.]+|{NUM}|--)\s+({NUM}|--)\s+([\d.]+|--)\s+(\S+)')
rows = []
def pages(a, b):
    for p in range(a, b + 1):
        yield p, r.pages[p - 1].extract_text().splitlines()
def lab(p): return str(p - 24)
# Table 1: PDF 30-38
buf = []; bufp = None
for p, lines in pages(30, 38):
    for ln in lines:
        s = ln.strip()
        if re.match(r'^[A-Z][A-Z0-9]*-', s) or re.match(r'^[A-Z][A-Za-z /&()-]+ \([A-Z]+\) [A-Z]+-', s):
            if not buf or not buf[-1].endswith('-'):
                buf = []; bufp = p
        if buf is not None:
            buf.append(s)
        m = end1.search(s)
        if m and buf:
            rec = ' '.join(buf); buf = []
            rec = re.sub(r'^.*?\b(?=[A-Z]{2,5}-)', '', rec, count=1) if not re.match(r'^[A-Z]{2,5}-', rec) else rec
            rec = re.sub(r'- (CCW|AFW)\b', r'-\1', rec)
            code = rec.split()[0]
            if not re.match(COMP + '-', code) or re.search(r'-(SWS|CWS)$|^PIPE-SWS', code): continue
            u, ncomp, dist, analise, p05, med, mean, p95, a, b, ef, dr = m.groups()
            unid = {'d': 'por demanda', 'h': 'por hora', 'h-ft': 'por hora-pé'}[u]
            desc = rec[len(code):m.start() + (len(rec) - len(s))].strip()
            obs = f'Table 1; analise={analise}; mediana={med}; EF={ef}; periodo={dr}; desc="{desc[:90]}"'
            if dist == 'Beta' and u != 'd':
                obs += '; conferir: distribuição Beta (prob. por demanda), mas a coluna d/h da Table 1 indica "h"'
                unid = 'conferir (Table 1 indica h)'
            if '(note c)' in rec: obs += '; note c: ELL/ILL derivado de ELS/ILS (NUREG/CR-6928)'
            if '(note d)' in rec: obs += '; note d: STF estimado com dados de STL'
            rows.append([PART, bufp, lab(bufp), 'Table 1', code.split('-')[0], code, dist,
                         a if a != '--' else '', b if b != '--' else '', mean, p05, p95, unid, obs])
# Table 2: PDF 40-41 (apenas linhas aplicaveis ao CCW + genericas de MDP/HTX)
ALVOS = [('MDP-ALL', r'MDP-ALL '), ('MDP-CLEAN', r'MDP-CLEAN '), ('MDP-NR-CLEAN', r'MDP-NR-\s*$'),
         ('MDP-CCW', r'MDP-CCW '), ('HTX', r'Pooled HTX '), ('HTX-CCW', r'HTX-CCW '), ('HDR-CCW', r'HDR-CCW ')]
for p, lines in pages(40, 41):
    lines = [l.strip() for l in lines]
    for i, s in enumerate(lines):
        for code, pat in ALVOS:
            if re.search(r'(^|\s)' + pat, s) and not (code == 'HTX' and 'CCW' in s):
                rec = ' '.join(lines[i:i + 7])
                m = end2.search(rec)
                if not m: print("SEM MATCH", p, code, rec[:200]); continue
                _, analise, ntrem, dist, p05, med, mean, p95, a, b, sd, ef, dr = m.groups()
                obs = (f'Table 2 (indisponibilidade T&M, por trem); analise={analise}; trens MSPI={ntrem}; '
                       f'mediana={med}; desvio_padrao={sd}; EF={ef}; periodo={dr}')
                if code == 'HTX': obs += '; linha "Pooled HTX" (genérica)'
                if code == 'HDR-CCW': obs += '; header (cabeçalho/coletor) do CCW, sem evento correspondente na árvore'
                if p05.startswith('-'): obs += '; p05 negativo na tabela (ajuste Normal), transcrito como está'
                comp = code.split('-')[0]
                rows.append([PART, p, lab(p), 'Table 2', comp, f'{code} (T&M)', dist, '', '', mean,
                             p05, p95, 'probabilidade (indisponibilidade)', obs])
with open(OUT, 'a', newline='') as f:
    csv.writer(f).writerows(rows)
for row in rows: print(row[1], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])
print(len(rows), 'linhas')

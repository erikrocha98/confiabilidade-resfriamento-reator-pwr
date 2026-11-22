"""Monta dados/parametros_eventos.csv a partir de dados/extracao_bruta.csv.

Uso:
    python scripts/montar_parametros.py

Regras (decididas pelo grupo, ver dados/README.md, secao "Suposicoes da extracao"):

- Uma linha por evento basico (id_evento nao repete). Cada evento agrega TODOS
  os modos de falha aplicaveis do componente; os modos usados ficam em
  ``codigo_inl``/``modo_falha`` e o detalhamento em ``dados/conferencia.md``.
- Quando o relatorio tem versao especifica do CCW de um modo, ela substitui a
  versao generica (registrado em ``observacao``).
- Valores lidos da Table 1 do INL/EXT-21-65055 (fonte primaria, ver fontes.md).
- prob_missao de cada modo: P = media (demanda) ou P = 1 - exp(-lambda*t) (taxa),
  com t = tempo_missao_h de config/parametros_globais.yaml. PIPE: lambda e por
  hora-pe, multiplicado pelo comprimento por trem (SUPOSICAO, ver abaixo).
- prob_missao do evento: 1 - prod(1 - P_i) (modos independentes, em serie).
- Como o evento combina modos de tipos diferentes, ``tipo``, ``distribuicao``,
  ``param_alfa``, ``param_beta``, ``media``, ``p05``, ``p95`` e ``unidade``
  ficam vazios; os parametros de cada modo estao em extracao_bruta.csv.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ccws import arvore as mod_arvore  # noqa: E402
from ccws import dados as mod_dados  # noqa: E402

FONTE = "INL/EXT-21-65055"

# SUPOSICAO: Table 175 (PDF 180, p. A-121) da 4008 pes de tubulacao (>= 2 pol.) por
# planta para o CCW de PWR. Dividimos igualmente entre os 2 trens da arvore.
PES_CCW_PLANTA = 4008
PES_POR_TREM = PES_CCW_PLANTA / 2

# Modos usados por componente: (codigo INL na Table 1, rotulo curto, motivo da escolha).
MODOS = {
    "MOV": [
        ("MOV-FTOC", "FTOC", "falha ao abrir ou fechar (combinado; usado no lugar de FTO e FTC separados)"),
        ("MOV-SOP-CCW", "SOP (CCW)", "versao CCW no lugar de MOV-SOP generico"),
        ("MOV-ILS", "ILS", ""), ("MOV-ILL", "ILL", ""), ("MOV-ELS", "ELS", ""), ("MOV-ELL", "ELL", ""),
    ],
    "CKV": [
        ("CKV-FTO", "FTO", "CKV nao tem FTOC no relatorio"), ("CKV-FTC", "FTC", ""),
        ("CKV-SOP", "SOP", ""), ("CKV-ILS", "ILS", ""), ("CKV-ILL", "ILL", ""),
        ("CKV-ELS", "ELS", ""), ("CKV-ELL", "ELL", ""),
    ],
    "XVM": [
        ("XVM-FTOC", "FTOC", ""), ("XVM-SOP", "SOP", ""), ("XVM-ILS", "ILS", ""),
        ("XVM-ILL", "ILL", ""), ("XVM-ELS", "ELS", ""), ("XVM-ELL", "ELL", ""),
    ],
    "FCV": [
        ("FCV-FTOC", "FTOC", ""), ("FCV-FC", "FC", ""), ("FCV-SOP", "SOP", "FCV nao tem modos de vazamento no relatorio"),
    ],
    "MDP": [
        ("MDP-FTS-CCW", "FTS (CCW)", "versao CCW no lugar de MDP-FTS-NS/NR genericos"),
        ("MDP-FTR-CCW", "FTR (CCW)", "versao CCW no lugar de MDP-FTR<1H/>1H/NR genericos"),
        ("MDP-ELS", "ELS", ""), ("MDP-ELL", "ELL", ""),
    ],
    "HTX": [
        ("HTX-PG-CCW", "PG (CCW)", "versao CCW (plugging) no lugar de HTX-LOHT generico; alternativa HTX-PG-NE-CCW nao usada"),
        ("HTX-ILS", "ILS", ""), ("HTX-ILL", "ILL", ""), ("HTX-ELS", "ELS", ""), ("HTX-ELL", "ELL", ""),
    ],
    "PIPE": [
        ("PIPE-OTHER-ELS", "ELS", "PIPE nao-service-water"), ("PIPE-OTHER-ELL", "ELL", ""),
    ],
}
for _s in ("STF", "STL", "STP", "STT"):
    MODOS[_s] = [(f"{_s}-FTOP-D", "FTOP (demanda)", ""), (f"{_s}-FTOP-R", "FTOP (por hora)", "")]


def prob_modo(linha: dict, t: float) -> tuple[float, str]:
    """Probabilidade do modo no tempo de missao e a formula usada (texto)."""
    media = float(linha["media"])
    if linha["distribuicao"] == "Beta":
        return media, "P = media (demanda)"
    if linha["unidade"] == "por hora-pé":
        lam = media * PES_POR_TREM
        return 1 - math.exp(-lam * t), f"P = 1-exp(-{media:.3E}*{PES_POR_TREM:g}ft*{t:g}h)"
    return 1 - math.exp(-media * t), f"P = 1-exp(-{media:.3E}*{t:g}h)"


def main() -> int:
    t = float(mod_dados.carregar_config()["tempo_missao_h"])
    arvore = mod_arvore.carregar_arvore()

    with open(RAIZ / "dados" / "extracao_bruta.csv", newline="") as f:
        t1 = {r["modo_falha"]: r for r in csv.DictReader(f) if r["tabela"] == "Table 1"}

    saida, detalhe = [], {}
    for id_evento in arvore.lista_eventos_basicos():
        info = arvore.info_eventos_basicos[id_evento]
        comp, trem = info["componente"], info["trem"]
        modos, paginas, notas, conferir, nao_achados = [], [], [], [], []
        q = 1.0
        for codigo, rotulo, motivo in MODOS[comp]:
            linha = t1.get(codigo)
            if linha is None:
                nao_achados.append(codigo)
                continue
            p, formula = prob_modo(linha, t)
            q *= 1 - p
            modos.append((codigo, rotulo, linha, p, formula))
            pag = f"Table 1, p. {linha['pagina_impressa']} (PDF p. {linha['pagina_pdf']})"
            if pag not in paginas:
                paginas.append(pag)
            if motivo:
                notas.append(f"{codigo}: {motivo}")
            if "conferir" in linha["observacao"]:
                conferir.append(codigo)
        obs = [f"{len(modos)} modos combinados: prob_missao = 1 - prod(1 - P_i), t = {t:g} h"]
        obs += notas
        if comp == "PIPE":
            obs.append(f"SUPOSICAO: comprimento = {PES_CCW_PLANTA} ft/planta (Table 175, PDF p. 180) / 2 trens = "
                       f"{PES_POR_TREM:g} ft por trem; ver dados/README.md")
        if comp == "STF":
            obs.append("STF estimado com dados de STL (note d da Table 1)")
        if conferir:
            obs.append("conferir: " + ", ".join(conferir) + " (ver extracao_bruta.csv)")
        if nao_achados:
            obs.append("não encontrado: " + ", ".join(nao_achados))
        obs.append("parametros por modo em dados/extracao_bruta.csv e dados/conferencia.md")
        saida.append({
            "id_evento": id_evento, "trem": trem, "componente": comp,
            "codigo_inl": "; ".join(m[0] for m in modos),
            "modo_falha": "; ".join(m[1] for m in modos),
            "tipo": "", "distribuicao": "", "param_alfa": "", "param_beta": "",
            "media": "", "p05": "", "p95": "", "unidade": "",
            "prob_missao": f"{1 - q:.4E}" if modos else "",
            "fonte": FONTE, "pagina_tabela": "; ".join(paginas),
            "observacao": "; ".join(obs),
        })
        detalhe[id_evento] = modos

    with open(RAIZ / "dados" / "parametros_eventos.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=mod_dados.COLUNAS_PARAMETROS_EVENTOS)
        w.writeheader()
        w.writerows(saida)
    for s in saida:
        print(f"{s['id_evento']:<7} {s['prob_missao']:>11}  {s['codigo_inl']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

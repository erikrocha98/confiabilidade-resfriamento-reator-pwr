"""Divide um PDF em partes de no máximo N páginas.

Uso:
    python scripts/dividir_pdf.py docs/AvgPara2020.pdf 100 [--saida dados/brutos/partes]

Gera arquivos nomeados pelo intervalo de páginas (numeração do PDF, base 1),
ex.: AvgPara2020_p001-100.pdf, AvgPara2020_p101-200.pdf.
"""

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter

SAIDA_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "brutos" / "partes"


def dividir_pdf(caminho: Path, tamanho: int, saida: Path) -> list[Path]:
    if tamanho < 1:
        raise ValueError("o tamanho da parte deve ser >= 1")
    leitor = PdfReader(str(caminho))
    total = len(leitor.pages)
    largura = max(3, len(str(total)))
    saida.mkdir(parents=True, exist_ok=True)

    gerados = []
    for inicio in range(0, total, tamanho):
        fim = min(inicio + tamanho, total)
        escritor = PdfWriter()
        for i in range(inicio, fim):
            escritor.add_page(leitor.pages[i])
        nome = f"{caminho.stem}_p{inicio + 1:0{largura}d}-{fim:0{largura}d}.pdf"
        destino = saida / nome
        with open(destino, "wb") as f:
            escritor.write(f)
        gerados.append(destino)
    return gerados


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pdf", type=Path, help="caminho do PDF de entrada")
    p.add_argument("tamanho", type=int, help="número máximo de páginas por parte")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="diretório de saída")
    args = p.parse_args()

    total = len(PdfReader(str(args.pdf)).pages)
    partes = dividir_pdf(args.pdf, args.tamanho, args.saida)
    print(f"{args.pdf.name}: {total} páginas -> {len(partes)} partes em {args.saida}")
    for parte in partes:
        n = len(PdfReader(str(parte)).pages)
        print(f"  {parte.name}  ({n} páginas, {parte.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

"""Frente 3 - Determinacao dos cortes minimos da arvore de falhas do CCWS.

O que este arquivo deve fazer:

- Ler a arvore de falhas via ``ccws.arvore``.
- Obter os cortes minimos (minimal cut sets) do evento topo, ou seja, os
  conjuntos minimos de eventos basicos cuja ocorrencia simultanea leva a perda
  da funcao de resfriamento.
- Reduzir os conjuntos obtidos aos minimos (descartar qualquer conjunto que
  contenha outro conjunto de corte).
- Salvar a lista de cortes em ``analitico/resultados/`` para uso da
  probabilidade do topo, das medidas de importancia e da frente 5.

Nada aqui esta implementado ainda: apenas a interface combinada com o grupo.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ccws import arvore as mod_arvore

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def obter_cortes_minimos(arvore: mod_arvore.ArvoreDeFalhas) -> list[frozenset[str]]:
    """Retorna os cortes minimos do evento topo.

    Args:
        arvore: arvore de falhas carregada de ``modelo/arvore_falhas.yaml``.

    Returns:
        Lista de conjuntos de ids de eventos basicos.
    """
    def expandir(no: str) -> list[frozenset[str]]:
        if no in arvore.info_eventos_basicos:
            return [frozenset({no})]

        porta = arvore.portas[no]
        entradas = [expandir(entrada) for entrada in porta["entradas"]]
        if porta["tipo"] == "OR":
            return reduzir_a_minimos([corte for grupo in entradas for corte in grupo])

        produto = [frozenset()]
        for grupo in entradas:
            produto = [anterior | atual for anterior in produto for atual in grupo]
            produto = reduzir_a_minimos(produto)
        return produto

    return ordenar_cortes(reduzir_a_minimos(expandir(arvore.evento_topo)))


def reduzir_a_minimos(cortes: list[frozenset[str]]) -> list[frozenset[str]]:
    """Remove conjuntos nao minimos (que contem outro corte como subconjunto)."""
    unicos = sorted(set(cortes), key=lambda c: (len(c), tuple(sorted(c))))
    minimos: list[frozenset[str]] = []
    for candidato in unicos:
        if not any(existente <= candidato for existente in minimos):
            minimos.append(candidato)
    return minimos


def ordenar_cortes(cortes: list[frozenset[str]]) -> list[frozenset[str]]:
    """Ordena cortes de forma deterministica por ordem e ids dos eventos."""
    return sorted(cortes, key=lambda c: (len(c), tuple(sorted(c))))


def conferir_com_funcao_estrutura(
    arvore: mod_arvore.ArvoreDeFalhas, cortes: list[frozenset[str]]
) -> bool:
    """Confere cada corte contra ``arvore.avalia``.

    Para todo corte: falhando exatamente os eventos do corte, o topo deve ocorrer;
    retirando qualquer um deles, o topo nao deve mais ocorrer (minimalidade).
    """
    for corte in cortes:
        if not arvore.avalia({evento: True for evento in corte}):
            return False
        for evento in corte:
            reduzido = corte - {evento}
            if arvore.avalia({item: True for item in reduzido}):
                return False
    return True


def salvar_cortes(cortes: list[frozenset[str]], caminho: Path | None = None) -> Path:
    """Salva os cortes minimos em ``analitico/resultados/cortes_minimos.csv``."""
    caminho = caminho or PASTA_RESULTADOS / "cortes_minimos.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id_corte", "ordem", "eventos"])
        for indice, corte in enumerate(ordenar_cortes(cortes), start=1):
            escritor.writerow([indice, len(corte), ";".join(sorted(corte))])
    return caminho


def carregar_cortes(caminho: Path | None = None) -> list[frozenset[str]]:
    """Carrega os cortes salvos por :func:`salvar_cortes`."""
    caminho = caminho or PASTA_RESULTADOS / "cortes_minimos.csv"
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return [
            frozenset(linha["eventos"].split(";"))
            for linha in csv.DictReader(arquivo)
        ]


def main() -> None:
    """Ponto de entrada: calcula, confere e salva os cortes minimos."""
    arvore = mod_arvore.carregar_arvore()
    cortes = obter_cortes_minimos(arvore)
    if not conferir_com_funcao_estrutura(arvore, cortes):
        raise RuntimeError("os cortes encontrados falharam na verificacao de minimalidade")
    caminho = salvar_cortes(cortes)
    contagem = Counter(map(len, cortes))
    resumo = ", ".join(f"ordem {ordem}: {quantidade}" for ordem, quantidade in sorted(contagem.items()))
    print(f"{len(cortes)} cortes minimos ({resumo})")
    print(f"salvo em: {caminho}")


if __name__ == "__main__":
    main()

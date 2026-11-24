"""Frente 3 - Probabilidade de ocorrencia do evento topo do CCWS.

O que este arquivo deve fazer:

- Ler ``config/parametros_globais.yaml`` (tempo de missao) e
  ``dados/parametros_eventos.csv`` via ``ccws.dados``.
- Converter o parametro de cada evento basico em probabilidade de falha no tempo
  de missao (``prob_missao``):
    - ``tipo = demanda``: a probabilidade e a propria media do INL;
    - ``tipo = taxa``: usar o modelo exponencial, 1 - exp(-lambda * t).
- Calcular a probabilidade do evento topo a partir dos cortes minimos
  (aproximacao de evento raro e/ou limite superior / inclusao-exclusao).
- Salvar os resultados em ``analitico/resultados/``.

Nada aqui esta implementado ainda.
"""

from __future__ import annotations

import math
import re
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ccws import arvore as mod_arvore
from ccws import dados as mod_dados
from analitico.cortes_minimos import carregar_cortes, obter_cortes_minimos

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def probabilidades_de_missao(
    parametros: pd.DataFrame, tempo_missao_h: float
) -> dict[str, float]:
    """Probabilidade de falha de cada evento basico no tempo de missao.

    Args:
        parametros: tabela de ``ccws.dados.carregar_parametros_eventos``.
        tempo_missao_h: tempo de missao em horas (da configuracao global).

    Returns:
        ``{id_evento: probabilidade}``.
    """
    if parametros.empty:
        raise mod_dados.ErroDados("a tabela de parametros de eventos esta vazia")

    resultado: dict[str, float] = {}
    for _, linha in parametros.iterrows():
        evento = linha.get("id_evento")
        if not isinstance(evento, str) or not evento:
            continue

        precomputada = linha.get("prob_missao")
        if pd.notna(precomputada):
            observacao = str(linha.get("observacao") or "")
            tempo_registrado = re.search(r"t\s*=\s*([0-9.]+)\s*h", observacao)
            if tempo_registrado and not math.isclose(
                float(tempo_registrado.group(1)), float(tempo_missao_h)
            ):
                raise mod_dados.ErroDados(
                    f"evento {evento}: prob_missao foi calculada para "
                    f"{tempo_registrado.group(1)} h, mas a configuracao pede "
                    f"{tempo_missao_h:g} h; recalcule os modos em extracao_bruta.csv"
                )
            probabilidade = float(precomputada)
        else:
            tipo = linha.get("tipo")
            media = linha.get("media")
            if pd.isna(media) or tipo not in {"demanda", "taxa"}:
                raise mod_dados.ErroDados(
                    f"evento {evento} sem prob_missao e sem tipo/media utilizaveis"
                )
            probabilidade = (
                float(media)
                if tipo == "demanda"
                else -math.expm1(-float(media) * float(tempo_missao_h))
            )

        if not 0.0 <= probabilidade <= 1.0:
            raise mod_dados.ErroDados(
                f"probabilidade de missao fora de [0, 1] para {evento}: {probabilidade}"
            )
        resultado[evento] = probabilidade
    return resultado


def probabilidade_topo_evento_raro(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> float:
    """Aproximacao de evento raro: soma das probabilidades dos cortes minimos."""
    return min(
        1.0,
        sum(math.prod(probabilidades[evento] for evento in corte) for corte in cortes),
    )


def probabilidade_topo_inclusao_exclusao(
    cortes: list[frozenset[str]], probabilidades: dict[str, float]
) -> float:
    """Probabilidade exata da uniao dos cortes, sob independencia.

    A expansao recursiva e uma forma fatorada de inclusao-exclusao (expansao de
    Shannon). Ela evita enumerar as 2^N intersecoes entre cortes.
    """
    faltantes = sorted({e for corte in cortes for e in corte} - set(probabilidades))
    if faltantes:
        raise KeyError("eventos sem probabilidade: " + ", ".join(faltantes))

    def normalizar(termos) -> tuple[tuple[str, ...], ...]:
        conjuntos = sorted(
            {frozenset(termo) for termo in termos},
            key=lambda termo: (len(termo), tuple(sorted(termo))),
        )
        minimos: list[frozenset[str]] = []
        for termo in conjuntos:
            if not any(anterior <= termo for anterior in minimos):
                minimos.append(termo)
        return tuple(tuple(sorted(termo)) for termo in minimos)

    @lru_cache(maxsize=None)
    def uniao(termos: tuple[tuple[str, ...], ...]) -> float:
        if not termos:
            return 0.0
        if any(len(termo) == 0 for termo in termos):
            return 1.0

        frequencia: dict[str, int] = {}
        for termo in termos:
            for evento in termo:
                frequencia[evento] = frequencia.get(evento, 0) + 1
        evento = max(frequencia, key=lambda item: (frequencia[item], item))

        com_evento = [set(termo) - {evento} for termo in termos if evento in termo]
        sem_evento = [set(termo) for termo in termos if evento not in termo]
        quando_falha = normalizar(com_evento + sem_evento)
        quando_funciona = normalizar(sem_evento)
        p = probabilidades[evento]
        return p * uniao(quando_falha) + (1.0 - p) * uniao(quando_funciona)

    return uniao(normalizar(cortes))


def salvar_resultados(resultados: dict, caminho: Path | None = None) -> Path:
    """Salva a probabilidade do topo e as probabilidades por evento em ``resultados/``."""
    caminho = caminho or PASTA_RESULTADOS / "prob_topo.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)

    probabilidades = resultados.pop("probabilidades_eventos")
    pd.DataFrame(
        [
            {"id_evento": evento, "prob_missao": probabilidade}
            for evento, probabilidade in sorted(probabilidades.items())
        ]
    ).to_csv(caminho.parent / "prob_eventos.csv", index=False)
    pd.DataFrame([resultados]).to_csv(caminho, index=False)
    return caminho


def main() -> None:
    """Ponto de entrada: calcula a probabilidade do topo e salva os resultados."""
    config = mod_dados.carregar_config()
    parametros = mod_dados.carregar_parametros_eventos()
    arvore = mod_arvore.carregar_arvore()
    tempo = float(config["tempo_missao_h"])
    probabilidades = probabilidades_de_missao(parametros, tempo)

    faltantes = sorted(set(arvore.lista_eventos_basicos()) - set(probabilidades))
    if faltantes:
        raise mod_dados.ErroDados("eventos sem probabilidade: " + ", ".join(faltantes))

    caminho_cortes = PASTA_RESULTADOS / "cortes_minimos.csv"
    cortes = carregar_cortes(caminho_cortes) if caminho_cortes.exists() else obter_cortes_minimos(arvore)
    exata = probabilidade_topo_inclusao_exclusao(cortes, probabilidades)
    rara = probabilidade_topo_evento_raro(cortes, probabilidades)
    resultados = {
        "tempo_missao_h": tempo,
        "prob_topo_exata_independencia": exata,
        "confiabilidade_sistema": 1.0 - exata,
        "limite_superior_cortes": rara,
        "erro_relativo_limite_superior": (rara - exata) / exata if exata else 0.0,
        "hipotese": "eventos basicos independentes; CCF nao integrada a arvore",
        "probabilidades_eventos": probabilidades,
    }
    caminho = salvar_resultados(resultados)
    print(f"P(topo) exata sob independencia = {exata:.10e}")
    print(f"R(sistema) = {1.0 - exata:.10f}")
    print(f"limite superior pelos cortes = {rara:.10e}")
    print(f"salvo em: {caminho}")


if __name__ == "__main__":
    main()

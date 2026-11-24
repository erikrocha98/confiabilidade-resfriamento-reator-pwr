"""Testes da solucao analitica da arvore de falhas."""

from __future__ import annotations

import math

import pytest

from analitico.cortes_minimos import (
    conferir_com_funcao_estrutura,
    obter_cortes_minimos,
)
from analitico.importancia import birnbaum, fussell_vesely
from analitico.probabilidade_topo import (
    probabilidade_topo_evento_raro,
    probabilidade_topo_inclusao_exclusao,
    probabilidades_de_missao,
)
from ccws.arvore import carregar_arvore
from ccws.dados import carregar_parametros_eventos


def test_cortes_minimos_da_arvore_atual():
    arvore = carregar_arvore()
    cortes = obter_cortes_minimos(arvore)

    assert len(cortes) == 121
    assert sum(len(corte) == 2 for corte in cortes) == 100
    assert sum(len(corte) == 3 for corte in cortes) == 20
    assert sum(len(corte) == 4 for corte in cortes) == 1
    assert conferir_com_funcao_estrutura(arvore, cortes)


def test_probabilidade_exata_de_uniao_com_intersecao():
    cortes = [frozenset({"A"}), frozenset({"B"})]
    probabilidades = {"A": 0.1, "B": 0.2}

    assert probabilidade_topo_inclusao_exclusao(cortes, probabilidades) == pytest.approx(0.28)
    assert probabilidade_topo_evento_raro(cortes, probabilidades) == pytest.approx(0.30)


def test_probabilidade_atual_confere_com_fatoracao_por_trens():
    arvore = carregar_arvore()
    cortes = obter_cortes_minimos(arvore)
    probabilidades = probabilidades_de_missao(carregar_parametros_eventos(), 24.0)
    calculada = probabilidade_topo_inclusao_exclusao(cortes, probabilidades)

    serie_a = [
        "STL_A", "STP_A", "STT_A", "STF_A", "PIPE_A",
        "MOV_A", "XVM_A", "CKV_A", "FCV_A", "HTX_A",
    ]
    serie_b = [evento[:-1] + "B" for evento in serie_a]
    falha_a = 1.0 - math.prod(1.0 - probabilidades[e] for e in serie_a) * (
        1.0 - probabilidades["MDP_A"] * probabilidades["MDP_C"]
    )
    falha_b = 1.0 - math.prod(1.0 - probabilidades[e] for e in serie_b) * (
        1.0 - probabilidades["MDP_B"] * probabilidades["MDP_D"]
    )

    assert calculada == pytest.approx(falha_a * falha_b, rel=1e-12)


def test_importancias_em_sistema_or_simples():
    cortes = [frozenset({"A"}), frozenset({"B"})]
    probabilidades = {"A": 0.1, "B": 0.2}

    assert birnbaum(cortes, probabilidades) == pytest.approx({"A": 0.8, "B": 0.9})
    assert fussell_vesely(cortes, probabilidades) == pytest.approx(
        {"A": 0.08 / 0.28, "B": 0.18 / 0.28}
    )

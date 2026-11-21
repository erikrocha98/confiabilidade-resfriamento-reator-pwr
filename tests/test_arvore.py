"""Testes da arvore de falhas do CCWS (modulo ccws.arvore).

Os casos aqui sao a rede de seguranca do modelo: se alguem mexer em
modelo/arvore_falhas.yaml por engano, estes testes falham.
"""

from __future__ import annotations

import pytest

from ccws.arvore import ErroArvore, carregar_arvore

# Eventos basicos esperados: 10 por trem + 4 bombas = 24.
COMPONENTES_POR_TREM = ["STL", "STP", "STT", "STF", "PIPE", "MOV", "XVM", "CKV", "FCV", "HTX"]
EVENTOS_ESPERADOS = (
    [f"{c}_A" for c in COMPONENTES_POR_TREM]
    + [f"{c}_B" for c in COMPONENTES_POR_TREM]
    + ["MDP_A", "MDP_B", "MDP_C", "MDP_D"]
)


@pytest.fixture(scope="module")
def arvore():
    """Arvore de falhas carregada de modelo/arvore_falhas.yaml."""
    return carregar_arvore()


# --------------------------------------------------------------- estrutura
def test_arvore_tem_24_eventos_basicos(arvore):
    assert len(arvore.lista_eventos_basicos()) == 24


def test_eventos_basicos_sao_os_esperados(arvore):
    assert sorted(arvore.lista_eventos_basicos()) == sorted(EVENTOS_ESPERADOS)


def test_evento_topo_e_porta_and_dos_dois_trens(arvore):
    topo = arvore.portas[arvore.evento_topo]
    assert topo["tipo"] == "AND"
    assert sorted(topo["entradas"]) == ["TREM_A", "TREM_B"]


def test_bombas_estao_em_and_por_trem(arvore):
    assert arvore.portas["BOMBAS_A"]["tipo"] == "AND"
    assert sorted(arvore.portas["BOMBAS_A"]["entradas"]) == ["MDP_A", "MDP_C"]
    assert arvore.portas["BOMBAS_B"]["tipo"] == "AND"
    assert sorted(arvore.portas["BOMBAS_B"]["entradas"]) == ["MDP_B", "MDP_D"]


def test_trens_sao_portas_or_com_seis_entradas(arvore):
    for trem in ("TREM_A", "TREM_B"):
        assert arvore.portas[trem]["tipo"] == "OR"
        assert len(arvore.portas[trem]["entradas"]) == 6


# ---------------------------------------------------- funcao estrutura
def test_nenhuma_falha_nao_derruba_o_sistema(arvore):
    assert arvore.avalia({}) is False


def test_todas_as_falhas_derrubam_o_sistema(arvore):
    estados = {evento: True for evento in arvore.lista_eventos_basicos()}
    assert arvore.avalia(estados) is True


def test_falha_de_uma_bomba_sozinha_nao_derruba(arvore):
    # MDP_A esta em AND com MDP_C: sozinha nao derruba nem o trem A.
    assert arvore.avalia({"MDP_A": True}) is False


def test_falha_das_duas_bombas_do_trem_a_nao_derruba_o_sistema(arvore):
    # Derruba o trem A, mas o topo e AND: o trem B continua operando.
    assert arvore.avalia({"MDP_A": True, "MDP_C": True}) is False


def test_duas_bombas_do_trem_a_mais_valvula_do_trem_b_derruba(arvore):
    # Caso citado no enunciado: MDP_A + MDP_C (trem A) + MOV_B (trem B) = falha do sistema.
    estados = {"MDP_A": True, "MDP_C": True, "MOV_B": True}
    assert arvore.avalia(estados) is True


def test_um_evento_em_serie_de_cada_trem_derruba(arvore):
    # PIPE esta direto no OR do trem: um de cada trem basta.
    assert arvore.avalia({"PIPE_A": True, "PIPE_B": True}) is True


def test_dois_eventos_do_mesmo_trem_nao_derrubam(arvore):
    assert arvore.avalia({"PIPE_A": True, "HTX_A": True}) is False


def test_instrumentacao_de_cada_trem_derruba(arvore):
    assert arvore.avalia({"STL_A": True, "STT_B": True}) is True


def test_bombas_cruzadas_nao_derrubam_nenhum_trem(arvore):
    # MDP_A (trem A) e MDP_B (trem B) sao bombas de trens diferentes:
    # cada trem ainda tem uma bomba operando.
    assert arvore.avalia({"MDP_A": True, "MDP_B": True}) is False


@pytest.mark.parametrize(
    "estados, esperado",
    [
        ({"HTX_A": True, "FCV_B": True}, True),
        ({"STF_A": True, "XVM_B": True}, True),
        ({"CKV_A": True}, False),
        ({"MDP_B": True, "MDP_D": True, "MDP_A": True}, False),  # trem B cai, trem A nao
        ({"MDP_B": True, "MDP_D": True, "PIPE_A": True}, True),  # os dois trens caem
    ],
)
def test_casos_conhecidos_da_funcao_estrutura(arvore, estados, esperado):
    assert arvore.avalia(estados) is esperado


def test_avalia_recusa_evento_inexistente(arvore):
    with pytest.raises(ErroArvore):
        arvore.avalia({"MDP_Z": True})


# --------------------------------------------------------------- utilitarios
def test_descricao_de_evento_basico_e_de_porta(arvore):
    assert arvore.descricao("MDP_A")
    assert arvore.descricao("TREM_A")
    with pytest.raises(KeyError):
        arvore.descricao("NAO_EXISTE")


def test_carregar_arquivo_inexistente_da_erro(tmp_path):
    with pytest.raises(ErroArvore):
        carregar_arvore(tmp_path / "nao_existe.yaml")

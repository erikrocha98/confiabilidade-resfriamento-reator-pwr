"""Testes da simulacao de Monte Carlo (Frente 4 - modulo monte_carlo.simulacao)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from scipy.linalg import expm

from ccws.arvore import ArvoreDeFalhas, ErroArvore, carregar_arvore
from ccws.dados import ErroDados, carregar_parametros_eventos
from monte_carlo import convergencia as conv
from monte_carlo import dinamico as din
from monte_carlo import simulacao as mc


@pytest.fixture(scope="module")
def arvore_ccws() -> ArvoreDeFalhas:
    return carregar_arvore()


# ----------------------------------------------------------- reprodutibilidade
def test_preparar_gerador_e_reprodutivel():
    g1 = mc.preparar_gerador(20262)
    g2 = mc.preparar_gerador(20262)
    np.testing.assert_array_equal(g1.random(50), g2.random(50))


def test_sortear_estados_extremos_0_e_1():
    eventos = ["E0", "E1"]
    probs = {"E0": 0.0, "E1": 1.0}
    estados = mc.sortear_estados(eventos, probs, mc.preparar_gerador(1), 500)
    assert estados.shape == (500, 2)
    assert estados.dtype == np.bool_
    assert not estados[:, 0].any()
    assert estados[:, 1].all()


def test_sortear_estados_valida_entradas():
    g = mc.preparar_gerador(1)
    with pytest.raises(ValueError):
        mc.sortear_estados(["A"], {"A": 0.5}, g, 0)
    with pytest.raises(ValueError):
        mc.sortear_estados(["A"], {"A": 1.2}, g, 10)
    with pytest.raises(KeyError):
        mc.sortear_estados(["A", "B"], {"A": 0.5}, g, 10)


# ----------------------------------------------------- equivalencia da arvore
def test_avaliar_historias_bate_100_por_cento_com_arvore_avalia(arvore_ccws):
    eventos = arvore_ccws.lista_eventos_basicos()
    # Probabilidades altas (0.25) para acionar todos os ramos da arvore.
    probs = {ev: 0.25 for ev in eventos}
    estados = mc.sortear_estados(eventos, probs, mc.preparar_gerador(42), 2_000)

    vetorizado = mc.avaliar_historias(arvore_ccws, eventos, estados)
    assert vetorizado.shape == (2_000,)
    assert vetorizado.dtype == np.bool_

    esperado = np.array(
        [
            arvore_ccws.avalia({ev: bool(linha[j]) for j, ev in enumerate(eventos)})
            for linha in estados
        ],
        dtype=bool,
    )
    np.testing.assert_array_equal(vetorizado, esperado)


def test_avaliar_historias_recusa_evento_inexistente_e_forma_invalida(arvore_ccws):
    with pytest.raises(ErroArvore):
        mc.avaliar_historias(arvore_ccws, ["MDP_Z"], np.zeros((5, 1), dtype=bool))
    with pytest.raises(ValueError):
        mc.avaliar_historias(arvore_ccws, ["MDP_A"], np.zeros((5, 2), dtype=bool))


# ----------------------------------------- validacao contra solucao analitica
def test_simulacao_base_converge_para_solucao_analitica_em_arvore_brinquedo():
    # Arvore simples: TOPO = AND(OR(A, B), C) -> P(TOPO) = (1 - (1-pA)(1-pB)) * pC
    dados_yaml = {
        "nome": "Teste",
        "evento_topo": "TOPO",
        "portas": {
            "TOPO": {"tipo": "AND", "entradas": ["G1", "C"]},
            "G1": {"tipo": "OR", "entradas": ["A", "B"]},
        },
        "eventos_basicos": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
    }
    arvore = ArvoreDeFalhas(dados_yaml)
    probs = {"A": 0.10, "B": 0.20, "C": 0.50}
    p_exato = (1.0 - (1.0 - 0.10) * (1.0 - 0.20)) * 0.50  # 0.14

    resumo, importancias = mc.rodar_simulacao_base(
        arvore=arvore,
        probabilidades=probs,
        n_historias=200_000,
        semente=12345,
        tamanho_lote=50_000,
    )

    assert resumo["n_historias"] == 200_000
    assert resumo["ic_wilson_inf"] <= p_exato <= resumo["ic_wilson_sup"]
    assert resumo["ic_clopper_pearson_inf"] <= p_exato <= resumo["ic_clopper_pearson_sup"]
    assert resumo["p_topo"] == pytest.approx(p_exato, rel=0.02)

    # C e obrigatorio para TOPO ocorrer -> P(C | TOPO) == 1.0
    fv_c = float(
        importancias.loc[importancias["id_evento"] == "C", "fussell_vesely_mc"].iloc[0]
    )
    assert fv_c == pytest.approx(1.0)


def test_lotes_diferentes_dao_mesmo_p_aproximado_e_mesma_semente_e_exata(arvore_ccws):
    eventos = arvore_ccws.lista_eventos_basicos()
    probs = {ev: 0.05 for ev in eventos}

    r1, imp1 = mc.rodar_simulacao_base(
        arvore_ccws, probs, n_historias=20_000, semente=77, tamanho_lote=5_000
    )
    r2, imp2 = mc.rodar_simulacao_base(
        arvore_ccws, probs, n_historias=20_000, semente=77, tamanho_lote=5_000
    )
    assert r1 == r2
    pd.testing.assert_frame_equal(imp1, imp2)


# -------------------------------------------- estimadores e intervalos (ICs)
def test_estimar_estatisticas_zero_falhas():
    est = mc.estimar_estatisticas_binomiais(n_falhas=0, n_historias=1_000)
    assert est["p_topo"] == 0.0
    assert est["erro_padrao"] == 0.0
    assert math.isnan(est["erro_relativo"])
    assert est["ic_wald_inf"] == 0.0
    assert est["ic_wald_sup"] == 0.0
    # Wilson e Clopper-Pearson mantem limite superior positivo mesmo com k=0.
    assert est["ic_wilson_inf"] == 0.0
    assert est["ic_wilson_sup"] > 0.0
    assert est["ic_clopper_pearson_inf"] == 0.0
    assert est["ic_clopper_pearson_sup"] > 0.0


def test_estimar_probabilidade_topo_consistente_com_estatisticas():
    vetor = np.array([False] * 990 + [True] * 10, dtype=bool)
    est = mc.estimar_probabilidade_topo(vetor)
    assert est["n_historias"] == 1_000
    assert est["n_falhas"] == 10
    assert est["p_topo"] == pytest.approx(0.01)
    assert est["ic_clopper_pearson_inf"] < est["p_topo"] < est["ic_clopper_pearson_sup"]
    assert est["ic_wilson_inf"] < est["p_topo"] < est["ic_wilson_sup"]


# ----------------------------------------------- extracao e salvamento de CSV
def test_extrair_probabilidades_missao_dos_dados_reais(arvore_ccws):
    parametros = carregar_parametros_eventos()
    probs = mc.extrair_probabilidades_missao(
        parametros, arvore_ccws.lista_eventos_basicos()
    )
    assert len(probs) == 24
    assert all(0.0 < p < 1.0 for p in probs.values())


def test_extrair_probabilidades_missao_acusa_faltantes(arvore_ccws):
    tabela_vazia = pd.DataFrame(columns=["id_evento", "prob_missao"])
    with pytest.raises(ErroDados):
        mc.extrair_probabilidades_missao(tabela_vazia, arvore_ccws.lista_eventos_basicos())


def test_salvar_resultados_e_importancias(tmp_path):
    resumo = {
        "modelo": "redundancia_ativa",
        "n_historias": 1_000,
        "n_falhas": 5,
        "p_topo": 0.005,
        "erro_padrao": 0.00223,
        "erro_relativo": 0.446,
        "ic95_inf": 0.002,
        "ic95_sup": 0.012,
        "semente": 20262,
        "tempo_missao_h": 24.0,
    }
    arq_res = mc.salvar_resultados(resumo, tmp_path / "mc_resumo.csv")
    df_res = pd.read_csv(arq_res)
    assert len(df_res) == 1
    assert df_res.loc[0, "n_falhas"] == 5

    imp = pd.DataFrame(
        {"id_evento": ["STL_A"], "prob_missao": [8.17e-4], "falhas_no_topo": [2], "fussell_vesely_mc": [0.4]}
    )
    arq_imp = mc.salvar_importancias_mc(imp, tmp_path / "mc_importancias.csv")
    df_imp = pd.read_csv(arq_imp)
    assert list(df_imp.columns) == [
        "id_evento",
        "prob_missao",
        "falhas_no_topo",
        "fussell_vesely_mc",
    ]


# ---------------------------------------------------- estudo de convergencia
def test_curva_de_convergencia_historia_a_historia_e_checkpoints():
    falhas = np.array([False, True, False, False, True], dtype=bool)
    curva = conv.curva_de_convergencia(falhas)
    assert list(curva["n_historias"]) == [1, 2, 3, 4, 5]
    assert list(curva["n_falhas"]) == [0, 1, 1, 1, 2]
    assert curva.loc[4, "estimativa"] == pytest.approx(0.4)

    curva_cp = conv.curva_de_convergencia(falhas, checkpoints=[2, 5])
    assert list(curva_cp["n_historias"]) == [2, 5]
    assert list(curva_cp["n_falhas"]) == [1, 2]


def test_rodar_estudo_convergencia_bate_exatamente_com_simulacao_base(arvore_ccws):
    eventos = arvore_ccws.lista_eventos_basicos()
    probs = {ev: 0.05 for ev in eventos}

    resumo, _ = mc.rodar_simulacao_base(
        arvore_ccws, probs, n_historias=30_000, semente=99, tamanho_lote=10_000
    )
    curva = conv.rodar_estudo_convergencia(
        arvore_ccws, probs, n_historias=30_000, semente=99, tamanho_lote=10_000
    )

    ultimo = curva.iloc[-1]
    assert int(ultimo["n_historias"]) == resumo["n_historias"]
    assert int(ultimo["n_falhas"]) == resumo["n_falhas"]
    assert float(ultimo["estimativa"]) == pytest.approx(resumo["p_topo"])
    assert float(ultimo["ic_wilson_inf"]) == pytest.approx(resumo["ic_wilson_inf"])
    assert float(ultimo["ic_wilson_sup"]) == pytest.approx(resumo["ic_wilson_sup"])


def test_n_historias_necessario_exige_estabilidade_ate_o_final():
    # Erro cai abaixo de 0.10 em N=200, volta a subir em N=500 e estabiliza em N=1000.
    curva = pd.DataFrame(
        {
            "n_historias": [100, 200, 500, 1000, 2000],
            "erro_relativo": [float("nan"), 0.08, 0.12, 0.09, 0.06],
        }
    )
    assert conv.n_historias_necessario(curva, 0.10) == 1000
    assert conv.n_historias_necessario(curva, 0.05) is None


def test_n_historias_teorico_formulas_erro_padrao_e_ic():
    p = 1e-4
    n_se = conv.n_historias_teorico(p, 0.10, criterio="erro_padrao")
    n_ic = conv.n_historias_teorico(p, 0.10, criterio="ic", nivel_confianca=0.95)
    # (1 - 1e-4) / (1e-4 * 0.01) = 999_900
    assert n_se == 999_900
    # Para IC 95%, z^2 ~= 3.841459 -> ~3.84x maior que o criterio de erro padrao
    assert n_ic > 3.8 * n_se


def test_grafico_convergencia_e_salvar_curva_criam_arquivos(tmp_path):
    rng = mc.preparar_gerador(123)
    falhas = rng.random(5_000) < 0.05
    curva = conv.curva_de_convergencia(falhas)

    arq_csv = conv.salvar_curva(curva, tmp_path / "mc_convergencia.csv")
    arq_png = conv.grafico_convergencia(
        curva,
        caminho=tmp_path / "mc_convergencia.png",
        p_analitico=0.05,
        erro_relativo_alvo=0.10,
    )

    assert arq_csv.is_file()
    assert arq_png.is_file()
    assert arq_png.stat().st_size > 1_000
    df_lido = pd.read_csv(arq_csv)
    assert len(df_lido) == len(curva)


# ----------------------------------- extensao dinamica (standby + reparo DES)
def test_parametros_decompostos_batem_com_parametros_eventos_csv(arvore_ccws):
    params_comp = din.carregar_parametros_decompostos()
    tabela = carregar_parametros_eventos().set_index("id_evento")

    for ev in arvore_ccws.lista_eventos_basicos():
        comp = arvore_ccws.info_eventos_basicos[ev]["componente"]
        p_decomp = params_comp[comp].prob_missao_estatica(24.0)
        p_csv = float(tabela.loc[ev, "prob_missao"])
        # parametros_eventos.csv arredonda em 4 casas decimais cientificas (%.4E)
        assert p_decomp == pytest.approx(p_csv, rel=1e-3), ev


@pytest.mark.parametrize("principal_parte_em_t0", [False, True])
def test_standby_sem_reparo_bate_com_solucao_analitica_erlang(principal_parte_em_t0):
    # Parametros sinteticos de teste para validacao matematica (nao sao dados do INL).
    lam = 0.05
    q_fts = 0.10
    T = 10.0
    p_exato = din.prob_falha_standby_analitica(
        lam, q_fts, T, principal_parte_em_t0=principal_parte_em_t0
    )

    falhou, em_fim, _ = din.simular_par_bombas_standby(
        taxa_falha_h=lam,
        prob_demanda_partida=q_fts,
        tempo_missao_h=T,
        n_historias=80_000,
        gerador=mc.preparar_gerador(2026),
        mttr_h=None,
        principal_parte_em_t0=principal_parte_em_t0,
    )
    np.testing.assert_array_equal(falhou, em_fim)

    est = mc.estimar_probabilidade_topo(falhou)
    assert est["ic_wilson_inf"] <= p_exato <= est["ic_wilson_sup"]


@pytest.mark.parametrize("n_equipes", [1, 2])
def test_standby_com_reparo_bate_com_cadeia_de_markov_3_estados(n_equipes):
    # Validacao contra Cadeia de Markov Continua (3 estados: 2 UP, 1 UP, 0 UP).
    # Valores sinteticos usados apenas para verificar o motor DES.
    lam = 0.05
    mttr = 4.0
    mu = 1.0 / mttr
    T = 20.0

    # Matriz geradora Q para indisponibilidade pontual U(T)
    Q = np.array(
        [
            [-lam, lam, 0.0],
            [mu, -(lam + mu), lam],
            [0.0, n_equipes * mu, -n_equipes * mu],
        ]
    )
    u_exato = float(expm(Q * T)[0, 2])

    # Matriz absorvente (estado 2 absorvente) para nao-confiabilidade F(T)
    Q_abs = np.array(
        [
            [-lam, lam, 0.0],
            [mu, -(lam + mu), lam],
            [0.0, 0.0, 0.0],
        ]
    )
    f_exato = float(expm(Q_abs * T)[0, 2])

    falhou, em_fim, frac_down = din.simular_par_bombas_standby(
        taxa_falha_h=lam,
        prob_demanda_partida=0.0,
        tempo_missao_h=T,
        n_historias=60_000,
        gerador=mc.preparar_gerador(500 + n_equipes),
        mttr_h=mttr,
        fator_espera=0.0,
        principal_parte_em_t0=False,
        n_equipes_reparo=n_equipes,
    )

    est_f = mc.estimar_probabilidade_topo(falhou)
    est_u = mc.estimar_probabilidade_topo(em_fim)

    assert est_f["ic_wilson_inf"] <= f_exato <= est_f["ic_wilson_sup"]
    assert est_u["ic_wilson_inf"] <= u_exato <= est_u["ic_wilson_sup"]
    # Com reparo, a indisponibilidade pontual e media sao menores que a nao-confiabilidade F(T)
    assert float(np.mean(frac_down)) < est_f["p_topo"]


def test_sistema_completo_des_consistente_com_e_sem_reparo(arvore_ccws):
    # Parametros sinteticos altos para acionar falhas frequentes em 20.000 historias.
    params_sinteticos = {
        comp: din.ParametrosComponente(comp, prob_demanda=0.0, taxa_falha_h=0.005)
        for comp in din.MODOS_POR_COMPONENTE
    }
    params_sinteticos["MDP"] = din.ParametrosComponente(
        "MDP", prob_demanda=0.05, taxa_falha_h=0.04
    )
    T = 10.0

    # 1. Sem reparo: deve bater com solucao analitica exata da arvore com standby nas bombas
    p_bomba_par = din.prob_falha_standby_analitica(0.04, 0.05, T, False)
    p_comp_serie = 1.0 - math.exp(-0.005 * T)
    # Cada trem tem 10 eventos serie + 1 par de bombas em OR
    p_trem = 1.0 - ((1.0 - p_comp_serie) ** 10) * (1.0 - p_bomba_par)
    p_topo_exato = p_trem * p_trem

    res_sem = din.simular_sistema_completo_des(
        arvore=arvore_ccws,
        parametros_comp=params_sinteticos,
        tempo_missao_h=T,
        n_historias=25_000,
        semente=321,
        mttr_por_componente=None,
    )
    assert res_sem["ic95_missao_inf"] <= p_topo_exato <= res_sem["ic95_missao_sup"]
    assert res_sem["indisponibilidade_pontual_T"] == pytest.approx(res_sem["p_topo_missao"])

    # 2. Com reparo: indisponibilidade pontual e media caem significativamente
    mttr_sintetico = {comp: 2.0 for comp in din.MODOS_POR_COMPONENTE}
    res_com = din.simular_sistema_completo_des(
        arvore=arvore_ccws,
        parametros_comp=params_sinteticos,
        tempo_missao_h=T,
        n_historias=25_000,
        semente=321,
        mttr_por_componente=mttr_sintetico,
    )
    assert res_com["indisponibilidade_pontual_T"] < res_sem["indisponibilidade_pontual_T"]
    assert res_com["indisponibilidade_media"] < res_com["p_topo_missao"]


def test_tratar_bomba_reserva_nao_altera_outros_eventos(arvore_ccws):
    eventos = arvore_ccws.lista_eventos_basicos()
    estados = np.zeros((200, len(eventos)), dtype=bool)
    idx_stl = eventos.index("STL_A")
    estados[:, idx_stl] = True

    modificado = mc.tratar_bomba_reserva(
        estados, eventos, tempo_missao_h=24.0, gerador=mc.preparar_gerador(1)
    )
    assert modificado.shape == estados.shape
    assert modificado is not estados
    # Coluna nao-bomba preservada intacta
    np.testing.assert_array_equal(modificado[:, idx_stl], estados[:, idx_stl])
    # Pares de bombas sincronizados (MDP_A == MDP_C e MDP_B == MDP_D)
    np.testing.assert_array_equal(
        modificado[:, eventos.index("MDP_A")], modificado[:, eventos.index("MDP_C")]
    )
    np.testing.assert_array_equal(
        modificado[:, eventos.index("MDP_B")], modificado[:, eventos.index("MDP_D")]
    )


def test_carregar_mttr_csv_exige_fonte_e_pagina(tmp_path):
    # CSV valido (com linha em branco permitida e linha com fonte/pagina)
    arq_ok = tmp_path / "mttr_ok.csv"
    arq_ok.write_text(
        "componente,mttr_h,fonte,pagina_tabela,observacao\n"
        "MDP,12.0,FONTE-TESTE,Tabela 1,linha de teste\n"
        "MOV,,,,em branco\n",
        encoding="utf-8",
    )
    assert din.carregar_mttr_csv(arq_ok) == {"MDP": 12.0}

    # CSV com numero sem fonte deve ser recusado
    arq_sem_fonte = tmp_path / "mttr_sem_fonte.csv"
    arq_sem_fonte.write_text(
        "componente,mttr_h,fonte,pagina_tabela\n"
        "MDP,12.0,,Tabela 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ErroDados, match="fonte"):
        din.carregar_mttr_csv(arq_sem_fonte)

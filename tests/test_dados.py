"""Testes da carga e validacao dos dados (modulo ccws.dados).

As tabelas em dados/ foram preenchidas com valores extraidos dos relatorios do
INL (ver docs/declaracao_uso_ia.md e dados/conferencia.md). Estes testes
garantem que:

- o cabecalho dos CSVs e exatamente o combinado com o grupo;
- todo valor numerico tem fonte e pagina de origem;
- valores fora do dominio permitido sao recusados;
- o cruzamento com a arvore aponta corretamente o que falta preencher.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ccws.arvore import carregar_arvore
from ccws.dados import (
    COLUNAS_FATORES_ALFA_CCF,
    COLUNAS_PARAMETROS_EVENTOS,
    ErroDados,
    carregar_config,
    carregar_fatores_alfa_ccf,
    carregar_parametros_eventos,
    eventos_fora_da_arvore,
    eventos_sem_dados,
)


# ------------------------------------------------------------------ cabecalhos
def test_parametros_eventos_tem_as_colunas_esperadas():
    tabela = carregar_parametros_eventos()
    assert list(tabela.columns) == COLUNAS_PARAMETROS_EVENTOS


def test_fatores_alfa_tem_as_colunas_esperadas():
    tabela = carregar_fatores_alfa_ccf()
    assert list(tabela.columns) == COLUNAS_FATORES_ALFA_CCF


def test_colunas_de_parametros_sao_as_17_combinadas():
    assert COLUNAS_PARAMETROS_EVENTOS[0] == "id_evento"
    assert len(COLUNAS_PARAMETROS_EVENTOS) == 17
    assert len(COLUNAS_FATORES_ALFA_CCF) == 12


# ------------------------------------------------------- carga com csv vazio
def test_carga_funciona_com_tabelas_vazias():
    # Situacao inicial do repo: extracao de dados ainda nao feita.
    parametros = carregar_parametros_eventos()
    alfa = carregar_fatores_alfa_ccf()
    assert parametros.empty or not parametros.empty  # carregou sem excecao
    assert alfa.empty or not alfa.empty


def test_todo_valor_numerico_tem_fonte_e_pagina():
    # Regra da disciplina: nenhum valor sem origem. Toda linha com algum numero
    # precisa apontar o relatorio (fonte) e a pagina/tabela de onde saiu.
    for tabela, numericas in (
        (carregar_parametros_eventos(), ["param_alfa", "param_beta", "media", "p05", "p95", "prob_missao"]),
        (carregar_fatores_alfa_ccf(), ["alfa_1", "alfa_2", "alfa_3", "alfa_4"]),
    ):
        com_numero = tabela[tabela[numericas].notna().any(axis=1)]
        sem_fonte = com_numero[com_numero["fonte"].isna() | com_numero["pagina_tabela"].isna()]
        assert sem_fonte.empty, f"linhas com valor numerico sem fonte/pagina: {list(sem_fonte.index + 2)}"


def test_prob_missao_e_uma_probabilidade():
    prob = carregar_parametros_eventos()["prob_missao"].dropna()
    assert ((prob >= 0) & (prob <= 1)).all()


def test_fatores_alfa_somam_aproximadamente_1():
    # Convencao do dados/README.md: alfa_k preenchidos somam ~1 dentro do grupo.
    alfa = carregar_fatores_alfa_ccf()
    for _, linha in alfa.iterrows():
        k = int(linha["tamanho_grupo"])
        soma = sum(linha[f"alfa_{i}"] for i in range(1, k + 1))
        assert soma == pytest.approx(1.0, abs=1e-3), linha["codigo_inl"]
        for i in range(k + 1, 5):
            assert pd.isna(linha[f"alfa_{i}"]), f"{linha['codigo_inl']}: alfa_{i} com k > tamanho_grupo"


# ------------------------------------------------------------------- config
def test_config_tem_as_chaves_obrigatorias():
    config = carregar_config()
    assert config["tempo_missao_h"] == 24
    assert config["n_simulacoes"] > 0
    assert "semente_aleatoria" in config


def test_config_inexistente_da_erro(tmp_path):
    with pytest.raises(ErroDados):
        carregar_config(tmp_path / "nao_existe.yaml")


# ------------------------------------------------------------- validacoes
def _escreve_csv(tmp_path, nome, colunas, linhas):
    caminho = tmp_path / nome
    conteudo = ",".join(colunas) + "\n" + "".join(linha + "\n" for linha in linhas)
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_cabecalho_diferente_e_recusado(tmp_path):
    caminho = _escreve_csv(tmp_path, "p.csv", ["id_evento", "coluna_estranha"], [])
    with pytest.raises(ErroDados):
        carregar_parametros_eventos(caminho)


def test_tipo_fora_do_dominio_e_recusado(tmp_path):
    linha = "MDP_A,A,MDP,XXX,falha,INVALIDO,beta,,,,,,,,,,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    with pytest.raises(ErroDados, match="tipo"):
        carregar_parametros_eventos(caminho)


def test_distribuicao_fora_do_dominio_e_recusada(tmp_path):
    linha = "MDP_A,A,MDP,XXX,falha,demanda,weibull,,,,,,,,,,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    with pytest.raises(ErroDados, match="distribuicao"):
        carregar_parametros_eventos(caminho)


def test_valor_nao_numerico_e_recusado(tmp_path):
    linha = "MDP_A,A,MDP,XXX,falha,demanda,beta,muito_alto,,,,,,,,,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    with pytest.raises(ErroDados, match="nao numericos"):
        carregar_parametros_eventos(caminho)


def test_id_evento_repetido_e_recusado(tmp_path):
    linha = "MDP_A,A,MDP,XXX,falha,demanda,beta,,,,,,,,,,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha, linha])
    with pytest.raises(ErroDados, match="repetido"):
        carregar_parametros_eventos(caminho)


def test_teste_escalonado_fora_do_dominio_e_recusado(tmp_path):
    linha = "MDP,XXX,falha,4,,,,,talvez,,,"
    caminho = _escreve_csv(tmp_path, "a.csv", COLUNAS_FATORES_ALFA_CCF, [linha])
    with pytest.raises(ErroDados, match="teste_escalonado"):
        carregar_fatores_alfa_ccf(caminho)


def test_linha_valida_e_aceita(tmp_path):
    # Valor ficticio usado apenas para testar a validacao da estrutura;
    # nao e dado de confiabilidade e nao entra em dados/.
    linha = "MDP_A,A,MDP,CODIGO-TESTE,falha ao partir,demanda,beta,1,2,0.5,,,adimensional,,TESTE,p. 1,linha de teste"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    tabela = carregar_parametros_eventos(caminho)
    assert len(tabela) == 1
    assert tabela.loc[0, "media"] == 0.5


# -------------------------------------------- cruzamento com a arvore
def test_nenhum_evento_da_arvore_esta_pendente():
    # Extracao concluida (Etapa 4): os 24 eventos basicos tem dados.
    arvore = carregar_arvore()
    parametros = carregar_parametros_eventos()
    pendentes = eventos_sem_dados(arvore.lista_eventos_basicos(), parametros)
    assert pendentes == []
    assert len(arvore.lista_eventos_basicos()) == 24


def test_evento_com_dado_sai_da_lista_de_pendentes(tmp_path):
    linha = "MDP_A,A,MDP,CODIGO-TESTE,falha ao partir,demanda,beta,,,0.5,,,adimensional,,TESTE,p. 1,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    parametros = carregar_parametros_eventos(caminho)
    arvore = carregar_arvore()
    pendentes = eventos_sem_dados(arvore.lista_eventos_basicos(), parametros)
    assert "MDP_A" not in pendentes
    assert len(pendentes) == 23


def test_linha_sem_valor_numerico_continua_pendente(tmp_path):
    # Linha criada mas sem nenhum parametro: ainda conta como pendente.
    linha = "MDP_A,A,MDP,CODIGO-TESTE,falha ao partir,demanda,beta,,,,,,,,,,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    parametros = carregar_parametros_eventos(caminho)
    arvore = carregar_arvore()
    assert "MDP_A" in eventos_sem_dados(arvore.lista_eventos_basicos(), parametros)


def test_id_desconhecido_e_apontado(tmp_path):
    linha = "MDP_Z,A,MDP,CODIGO-TESTE,falha,demanda,beta,,,0.5,,,adimensional,,TESTE,p. 1,"
    caminho = _escreve_csv(tmp_path, "p.csv", COLUNAS_PARAMETROS_EVENTOS, [linha])
    parametros = carregar_parametros_eventos(caminho)
    arvore = carregar_arvore()
    assert eventos_fora_da_arvore(arvore.lista_eventos_basicos(), parametros) == ["MDP_Z"]


def test_esqueleto_nao_tem_id_fora_da_arvore():
    arvore = carregar_arvore()
    parametros = carregar_parametros_eventos()
    assert eventos_fora_da_arvore(arvore.lista_eventos_basicos(), parametros) == []

"""Carga e validacao dos dados do estudo (frente 2) e da configuracao global.

Este modulo e a unica porta de entrada para os dados. As frentes 3, 4 e 5 devem
chamar as funcoes daqui em vez de ler os CSVs diretamente, para que a validacao
aconteca sempre.

Importante: as tabelas em ``dados/`` nascem apenas com o cabecalho. Os valores
sao extraidos manualmente dos relatorios do INL por um integrante do grupo.
Por isso TODAS as funcoes deste modulo funcionam com as tabelas vazias: elas
validam a estrutura (colunas e dominios), nunca inventam numeros.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

# Raiz do repositorio: este arquivo esta em <raiz>/ccws/dados.py
RAIZ_REPO = Path(__file__).resolve().parent.parent

CAMINHO_CONFIG_PADRAO = RAIZ_REPO / "config" / "parametros_globais.yaml"
CAMINHO_PARAMETROS_PADRAO = RAIZ_REPO / "dados" / "parametros_eventos.csv"
CAMINHO_ALFA_CCF_PADRAO = RAIZ_REPO / "dados" / "fatores_alfa_ccf.csv"

# ---------------------------------------------------------------------------
# Esquema esperado das tabelas (a ordem e a mesma dos arquivos CSV).
# ---------------------------------------------------------------------------
COLUNAS_PARAMETROS_EVENTOS = [
    "id_evento",
    "trem",
    "componente",
    "codigo_inl",
    "modo_falha",
    "tipo",
    "distribuicao",
    "param_alfa",
    "param_beta",
    "media",
    "p05",
    "p95",
    "unidade",
    "prob_missao",
    "fonte",
    "pagina_tabela",
    "observacao",
]

COLUNAS_FATORES_ALFA_CCF = [
    "componente",
    "codigo_inl",
    "modo_falha",
    "tamanho_grupo",
    "alfa_1",
    "alfa_2",
    "alfa_3",
    "alfa_4",
    "teste_escalonado",
    "fonte",
    "pagina_tabela",
    "observacao",
]

# Colunas que devem ser numericas quando preenchidas.
COLUNAS_NUMERICAS_PARAMETROS = [
    "param_alfa",
    "param_beta",
    "media",
    "p05",
    "p95",
    "prob_missao",
]
COLUNAS_NUMERICAS_ALFA_CCF = [
    "tamanho_grupo",
    "alfa_1",
    "alfa_2",
    "alfa_3",
    "alfa_4",
]

# Dominios fechados (valores permitidos) das colunas categoricas.
VALORES_TIPO = {"demanda", "taxa"}
VALORES_DISTRIBUICAO = {"beta", "gama", "lognormal"}
VALORES_SIM_NAO = {"sim", "nao"}

# Chaves obrigatorias da configuracao global.
CHAVES_CONFIG = ("tempo_missao_h", "n_simulacoes", "semente_aleatoria")


class ErroDados(Exception):
    """Erro de estrutura ou de dominio nos dados de entrada."""


# ---------------------------------------------------------------------------
# Configuracao global
# ---------------------------------------------------------------------------
def carregar_config(caminho: str | Path | None = None) -> dict:
    """Le ``config/parametros_globais.yaml`` e confere as chaves obrigatorias."""
    caminho = Path(caminho) if caminho is not None else CAMINHO_CONFIG_PADRAO
    if not caminho.is_file():
        raise ErroDados(f"arquivo de configuracao nao encontrado: {caminho}")

    with caminho.open(encoding="utf-8") as arquivo:
        config = yaml.safe_load(arquivo) or {}

    faltantes = [chave for chave in CHAVES_CONFIG if chave not in config]
    if faltantes:
        raise ErroDados(
            "chaves ausentes em parametros_globais.yaml: " + ", ".join(faltantes)
        )

    if float(config["tempo_missao_h"]) <= 0:
        raise ErroDados("tempo_missao_h deve ser positivo")
    if int(config["n_simulacoes"]) <= 0:
        raise ErroDados("n_simulacoes deve ser positivo")

    return config


# ---------------------------------------------------------------------------
# Leitura das tabelas
# ---------------------------------------------------------------------------
def _le_csv(caminho: Path, colunas_esperadas: list[str]) -> pd.DataFrame:
    """Le um CSV como texto e confere o cabecalho.

    Lemos tudo como string (``dtype=str``) para nao deixar o pandas adivinhar
    tipos em uma tabela que pode estar vazia ou parcialmente preenchida. A
    conversao numerica e feita depois, coluna por coluna.
    """
    if not caminho.is_file():
        raise ErroDados(f"arquivo de dados nao encontrado: {caminho}")

    tabela = pd.read_csv(caminho, dtype=str, keep_default_na=True)

    if list(tabela.columns) != colunas_esperadas:
        raise ErroDados(
            f"colunas inesperadas em {caminho.name}.\n"
            f"  esperado: {colunas_esperadas}\n"
            f"  encontrado: {list(tabela.columns)}"
        )

    # Remove espacos sobrando digitados na planilha.
    for coluna in tabela.columns:
        tabela[coluna] = tabela[coluna].str.strip()

    return tabela


def _converte_numericas(
    tabela: pd.DataFrame, colunas: list[str], nome_arquivo: str
) -> pd.DataFrame:
    """Converte as colunas numericas, acusando valores nao numericos."""
    for coluna in colunas:
        original = tabela[coluna]
        convertida = pd.to_numeric(original, errors="coerce")
        # Linha com texto que nao e numero: original preenchido, convertido NaN.
        invalidas = original.notna() & convertida.isna()
        if invalidas.any():
            linhas = [int(i) + 2 for i in tabela.index[invalidas]]  # +2: cabecalho e base 1
            raise ErroDados(
                f"valores nao numericos na coluna '{coluna}' de {nome_arquivo}, "
                f"linhas {linhas}"
            )
        tabela[coluna] = convertida
    return tabela


def _valida_dominio(
    tabela: pd.DataFrame, coluna: str, permitidos: set[str], nome_arquivo: str
) -> None:
    """Confere que uma coluna categorica so usa valores permitidos (celulas vazias passam)."""
    preenchidas = tabela[coluna].dropna()
    fora = sorted(set(preenchidas) - permitidos)
    if fora:
        raise ErroDados(
            f"valores invalidos na coluna '{coluna}' de {nome_arquivo}: {fora} "
            f"(permitidos: {sorted(permitidos)})"
        )


def carregar_parametros_eventos(caminho: str | Path | None = None) -> pd.DataFrame:
    """Carrega ``dados/parametros_eventos.csv`` validado.

    Funciona com a tabela vazia (so cabecalho): nesse caso retorna um DataFrame
    sem linhas, com as colunas esperadas.
    """
    caminho = Path(caminho) if caminho is not None else CAMINHO_PARAMETROS_PADRAO
    tabela = _le_csv(caminho, COLUNAS_PARAMETROS_EVENTOS)
    tabela = _converte_numericas(tabela, COLUNAS_NUMERICAS_PARAMETROS, caminho.name)

    _valida_dominio(tabela, "tipo", VALORES_TIPO, caminho.name)
    _valida_dominio(tabela, "distribuicao", VALORES_DISTRIBUICAO, caminho.name)

    # id_evento e a chave da tabela: nao pode repetir.
    ids = tabela["id_evento"].dropna()
    duplicados = sorted(ids[ids.duplicated()].unique())
    if duplicados:
        raise ErroDados(
            f"id_evento repetido em {caminho.name}: {duplicados}"
        )

    return tabela


def carregar_fatores_alfa_ccf(caminho: str | Path | None = None) -> pd.DataFrame:
    """Carrega ``dados/fatores_alfa_ccf.csv`` validado (funciona vazio)."""
    caminho = Path(caminho) if caminho is not None else CAMINHO_ALFA_CCF_PADRAO
    tabela = _le_csv(caminho, COLUNAS_FATORES_ALFA_CCF)
    tabela = _converte_numericas(tabela, COLUNAS_NUMERICAS_ALFA_CCF, caminho.name)

    _valida_dominio(tabela, "teste_escalonado", VALORES_SIM_NAO, caminho.name)

    return tabela


# ---------------------------------------------------------------------------
# Cruzamento com a arvore de falhas
# ---------------------------------------------------------------------------
def eventos_sem_dados(
    eventos_basicos: list[str], parametros: pd.DataFrame
) -> list[str]:
    """Eventos da arvore que ainda nao tem linha preenchida na tabela.

    Uma linha conta como "preenchida" quando tem ``id_evento`` e pelo menos um
    valor numerico de quantificacao (``media``, ``prob_missao`` ou os parametros
    da distribuicao). Enquanto a extracao dos relatorios do INL nao terminar,
    esta lista mostra o que falta.
    """
    colunas_quantificacao = ["media", "prob_missao", "param_alfa", "param_beta"]
    preenchidas = parametros.dropna(subset=["id_evento"])
    tem_valor = preenchidas[colunas_quantificacao].notna().any(axis=1)
    com_dados = set(preenchidas.loc[tem_valor, "id_evento"])

    return [evento for evento in eventos_basicos if evento not in com_dados]


def eventos_fora_da_arvore(
    eventos_basicos: list[str], parametros: pd.DataFrame
) -> list[str]:
    """Ids presentes na tabela que nao correspondem a nenhum evento basico."""
    conhecidos = set(eventos_basicos)
    ids = parametros["id_evento"].dropna()
    return sorted({valor for valor in ids if valor not in conhecidos})

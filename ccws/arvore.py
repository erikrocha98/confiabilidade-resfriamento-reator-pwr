"""Leitura e avaliacao da arvore de falhas do CCWS.

Este modulo e deliberadamente simples: todo o grupo precisa conseguir explicar
o que ele faz. Ele tem tres responsabilidades:

1. Carregar ``modelo/arvore_falhas.yaml`` (frente 1).
2. Dizer quais sao os eventos basicos (as folhas da arvore).
3. Avaliar a "funcao estrutura": dado quais eventos basicos falharam,
   responder se o evento topo ocorre ou nao.

A funcao estrutura e usada tanto pela frente 4 (Monte Carlo, uma avaliacao por
historia sorteada) quanto pelos testes da frente 3 (conferir cortes minimos).
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Raiz do repositorio: este arquivo esta em <raiz>/ccws/arvore.py
RAIZ_REPO = Path(__file__).resolve().parent.parent
CAMINHO_ARVORE_PADRAO = RAIZ_REPO / "modelo" / "arvore_falhas.yaml"

# Tipos de porta logica aceitos no YAML.
TIPOS_DE_PORTA = ("AND", "OR")


class ErroArvore(Exception):
    """Erro de estrutura da arvore de falhas (YAML mal formado ou inconsistente)."""


class ArvoreDeFalhas:
    """Representa a arvore de falhas carregada do YAML.

    Atributos:
        nome: nome do estudo / do evento topo, como escrito no YAML.
        evento_topo: id da porta de topo (ex.: ``"TOPO"``).
        portas: dicionario ``{id_da_porta: {"tipo": "AND"|"OR", "entradas": [...]}}``.
        eventos_basicos: lista de ids dos eventos basicos, na ordem do YAML.
    """

    def __init__(self, dados_yaml: dict):
        self.nome: str = dados_yaml.get("nome", "")
        self.evento_topo: str = dados_yaml["evento_topo"]
        self.portas: dict[str, dict] = dados_yaml["portas"]

        # Guardamos os eventos basicos de duas formas: a lista de ids (para
        # iterar em ordem estavel) e o dicionario completo (para descricoes).
        self.info_eventos_basicos: dict[str, dict] = {
            evento["id"]: evento for evento in dados_yaml["eventos_basicos"]
        }
        self.eventos_basicos: list[str] = list(self.info_eventos_basicos)

        self._valida()

    # ------------------------------------------------------------------ carga
    @classmethod
    def carregar(cls, caminho: str | Path | None = None) -> "ArvoreDeFalhas":
        """Carrega a arvore a partir de um arquivo YAML.

        Se ``caminho`` for omitido, usa ``modelo/arvore_falhas.yaml``.
        """
        caminho = Path(caminho) if caminho is not None else CAMINHO_ARVORE_PADRAO
        if not caminho.is_file():
            raise ErroArvore(f"arquivo da arvore nao encontrado: {caminho}")

        with caminho.open(encoding="utf-8") as arquivo:
            dados_yaml = yaml.safe_load(arquivo)

        for chave in ("evento_topo", "portas", "eventos_basicos"):
            if chave not in dados_yaml:
                raise ErroArvore(f"chave obrigatoria ausente no YAML: {chave}")

        return cls(dados_yaml)

    # --------------------------------------------------------------- validacao
    def _valida(self) -> None:
        """Confere a coerencia interna da arvore antes de qualquer analise."""
        if self.evento_topo not in self.portas:
            raise ErroArvore(
                f"o evento topo '{self.evento_topo}' nao esta definido em 'portas'"
            )

        for id_porta, porta in self.portas.items():
            tipo = porta.get("tipo")
            if tipo not in TIPOS_DE_PORTA:
                raise ErroArvore(
                    f"porta '{id_porta}' tem tipo invalido: {tipo!r} "
                    f"(esperado um de {TIPOS_DE_PORTA})"
                )
            entradas = porta.get("entradas") or []
            if not entradas:
                raise ErroArvore(f"porta '{id_porta}' nao tem entradas")

            # Toda entrada precisa ser outra porta ou um evento basico conhecido.
            for entrada in entradas:
                if entrada not in self.portas and entrada not in self.info_eventos_basicos:
                    raise ErroArvore(
                        f"entrada '{entrada}' da porta '{id_porta}' nao e porta "
                        "nem evento basico declarado"
                    )

        # Um evento basico declarado mas nunca usado quase sempre e erro de digitacao.
        usados = {
            entrada
            for porta in self.portas.values()
            for entrada in porta["entradas"]
        }
        nao_usados = sorted(set(self.info_eventos_basicos) - usados)
        if nao_usados:
            raise ErroArvore(
                "eventos basicos declarados mas nao usados em nenhuma porta: "
                + ", ".join(nao_usados)
            )

    # --------------------------------------------------------------- consultas
    def lista_eventos_basicos(self) -> list[str]:
        """Retorna os ids dos eventos basicos (24 no modelo atual)."""
        return list(self.eventos_basicos)

    def lista_portas(self) -> list[str]:
        """Retorna os ids das portas logicas."""
        return list(self.portas)

    def descricao(self, id_evento: str) -> str:
        """Descricao textual de um evento basico ou de uma porta."""
        if id_evento in self.info_eventos_basicos:
            return self.info_eventos_basicos[id_evento].get("descricao", "")
        if id_evento in self.portas:
            return self.portas[id_evento].get("descricao", "")
        raise KeyError(f"evento desconhecido: {id_evento}")

    # -------------------------------------------------------- funcao estrutura
    def avalia(self, estados: dict[str, bool]) -> bool:
        """Avalia a funcao estrutura da arvore.

        Args:
            estados: dicionario ``{id_do_evento_basico: True se falhou}``.
                Eventos basicos ausentes do dicionario sao tratados como
                ``False`` (componente operando). Isso deixa os testes curtos:
                basta listar o que falhou.

        Returns:
            ``True`` se o evento topo ocorre (sistema falha), ``False`` caso contrario.

        Levanta ``ErroArvore`` se o dicionario citar um evento que nao existe,
        o que normalmente indica erro de digitacao no id.
        """
        desconhecidos = sorted(set(estados) - set(self.info_eventos_basicos))
        if desconhecidos:
            raise ErroArvore(
                "estados informados para eventos que nao existem na arvore: "
                + ", ".join(desconhecidos)
            )

        return self._avalia_no(self.evento_topo, estados)

    def _avalia_no(self, id_no: str, estados: dict[str, bool]) -> bool:
        """Avalia um no da arvore recursivamente (porta ou evento basico)."""
        # Caso base: evento basico. Ausente no dicionario = nao falhou.
        if id_no in self.info_eventos_basicos:
            return bool(estados.get(id_no, False))

        porta = self.portas[id_no]
        # Avalia cada entrada da porta (que pode ser outra porta).
        valores = (self._avalia_no(entrada, estados) for entrada in porta["entradas"])

        if porta["tipo"] == "AND":
            return all(valores)
        return any(valores)  # OR


def carregar_arvore(caminho: str | Path | None = None) -> ArvoreDeFalhas:
    """Atalho para ``ArvoreDeFalhas.carregar`` (uso nas frentes 3, 4 e 5)."""
    return ArvoreDeFalhas.carregar(caminho)

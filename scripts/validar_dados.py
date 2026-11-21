"""Confere se os dados de entrada estao coerentes com a arvore de falhas.

Uso:

    python scripts/validar_dados.py

O script:

1. carrega ``modelo/arvore_falhas.yaml`` e valida a estrutura da arvore;
2. carrega ``dados/parametros_eventos.csv`` e ``dados/fatores_alfa_ccf.csv``
   (validando colunas e dominios);
3. lista os eventos basicos da arvore que **ainda nao tem linha preenchida** no CSV;
4. lista ids do CSV que nao correspondem a nenhum evento basico (erro de digitacao).

Com as tabelas vazias (situacao inicial do repo) ele roda sem erro e informa que
os 24 eventos estao pendentes. Codigo de saida 0 quando nao ha inconsistencia
estrutural, 1 quando ha.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o script direto, sem instalar o pacote.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ccws import arvore as mod_arvore  # noqa: E402
from ccws import dados as mod_dados  # noqa: E402


def main() -> int:
    print("=" * 70)
    print("Validacao dos dados do estudo de confiabilidade do CCWS")
    print("=" * 70)

    # ------------------------------------------------------------- 1. arvore
    try:
        arvore = mod_arvore.carregar_arvore()
    except mod_arvore.ErroArvore as erro:
        print(f"[ERRO] arvore de falhas invalida: {erro}")
        return 1

    eventos = arvore.lista_eventos_basicos()
    print(f"\nArvore: {arvore.nome}")
    print(f"  evento topo:      {arvore.evento_topo}")
    print(f"  portas:           {len(arvore.lista_portas())}")
    print(f"  eventos basicos:  {len(eventos)}")

    # -------------------------------------------------------------- 2. dados
    try:
        config = mod_dados.carregar_config()
        parametros = mod_dados.carregar_parametros_eventos()
        alfa_ccf = mod_dados.carregar_fatores_alfa_ccf()
    except mod_dados.ErroDados as erro:
        print(f"\n[ERRO] dados invalidos: {erro}")
        return 1

    print("\nConfiguracao global:")
    print(f"  tempo de missao:  {config['tempo_missao_h']} h")
    print(f"  n_simulacoes:     {config['n_simulacoes']}")
    print(f"  semente:          {config['semente_aleatoria']}")

    print("\nTabelas de dados (estrutura validada):")
    print(f"  parametros_eventos.csv: {len(parametros)} linha(s)")
    print(f"  fatores_alfa_ccf.csv:   {len(alfa_ccf)} linha(s)")

    # --------------------------------------------- 3. eventos sem dados ainda
    pendentes = mod_dados.eventos_sem_dados(eventos, parametros)
    print("\n" + "-" * 70)
    if pendentes:
        print(f"PENDENTE: {len(pendentes)} de {len(eventos)} eventos basicos sem dados preenchidos")
        print("(extrair dos relatorios do INL - ver dados/fontes.md)\n")
        for id_evento in pendentes:
            print(f"  [ ] {id_evento:<8} {arvore.descricao(id_evento)}")
    else:
        print(f"OK: todos os {len(eventos)} eventos basicos tem dados preenchidos")

    # -------------------------------------------------- 4. ids desconhecidos
    desconhecidos = mod_dados.eventos_fora_da_arvore(eventos, parametros)
    if desconhecidos:
        print("\n" + "-" * 70)
        print("[ERRO] ids em parametros_eventos.csv que nao existem na arvore:")
        for id_evento in desconhecidos:
            print(f"  {id_evento}")
        print("Conferir a grafia contra modelo/arvore_falhas.yaml.")
        return 1

    print("-" * 70)
    print("Validacao estrutural concluida sem erros.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

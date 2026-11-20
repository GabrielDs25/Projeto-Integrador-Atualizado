"""Carregamento e validação dos casos de teste."""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CASOS_PADRAO = RAIZ / "eval" / "casos.json"
PROMPTS_DIR = RAIZ / "eval" / "prompts"

SPLITS = ("calibracao", "teste")
CAMPOS_OBRIGATORIOS = ("id", "split", "pergunta", "resposta_referencia", "palavras_chave")


def validar_casos(casos):
    """Valida a estrutura dos casos e levanta ValueError se houver problema."""
    if not isinstance(casos, list) or not casos:
        raise ValueError("O arquivo de casos deve conter uma lista não vazia.")

    ids = set()
    for posicao, caso in enumerate(casos, start=1):
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if not caso.get(campo)]
        if faltando:
            raise ValueError(f"Caso na posição {posicao} sem os campos: {', '.join(faltando)}")
        if caso["split"] not in SPLITS:
            raise ValueError(f"Caso {caso['id']}: split inválido '{caso['split']}'")
        if caso["id"] in ids:
            raise ValueError(f"ID de caso repetido: {caso['id']}")
        if not isinstance(caso["palavras_chave"], list):
            raise ValueError(f"Caso {caso['id']}: palavras_chave deve ser uma lista")
        ids.add(caso["id"])

    return casos


def carregar_casos(caminho=CASOS_PADRAO, split=None, limite=None):
    """Lê os casos do JSON, filtrando opcionalmente por split e quantidade."""
    with open(caminho, encoding="utf-8") as arquivo:
        casos = validar_casos(json.load(arquivo))

    if split and split != "todos":
        if split not in SPLITS:
            raise ValueError(f"Split inválido: {split}. Use {', '.join(SPLITS)} ou todos.")
        casos = [caso for caso in casos if caso["split"] == split]

    if limite:
        casos = casos[:limite]

    return casos


def carregar_prompt(versao, pasta=PROMPTS_DIR):
    """Lê o prompt de sistema de uma versão (arquivo eval/prompts/<versao>.txt)."""
    caminho = Path(pasta) / f"{versao}.txt"
    if not caminho.exists():
        disponiveis = sorted(p.stem for p in Path(pasta).glob("*.txt"))
        raise FileNotFoundError(
            f"Versão de prompt '{versao}' não encontrada em {pasta}. "
            f"Disponíveis: {', '.join(disponiveis) or 'nenhuma'}"
        )
    return caminho.read_text(encoding="utf-8").strip()

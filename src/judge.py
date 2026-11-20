"""LLM como juiz: decide se a resposta de um modelo está correta.

O juiz recebe a pergunta, a resposta de referência e a resposta do modelo e
devolve um JSON com o veredito. A qualidade do juiz é medida contra notas
humanas (ver evaluation.concordancia).
"""

import json
import os
import re

from src.model_runner import chamar_modelo

JUIZ_PADRAO = "qwen2.5:7b"
VERSAO_PROMPT_JUIZ = "juiz-v1"

PROMPT_JUIZ = """Você é um avaliador rigoroso de respostas sobre programação.

Pergunta: <<PERGUNTA>>
Resposta de referência (correta): <<REFERENCIA>>
Resposta do modelo avaliado: <<RESPOSTA>>

Critério:
- APROVADA: a resposta do modelo traz a informação da resposta de referência de forma correta. Sinônimos, outro idioma, formatação diferente e explicações adicionais são aceitos, desde que não contradigam a referência.
- REPROVADA: a resposta está errada, é vaga ou evasiva, não traz a informação pedida, ou traz informações contraditórias.

Responda somente com um JSON no formato:
{"aprovado": true ou false, "justificativa": "uma frase curta explicando o motivo"}"""


def modelo_juiz_configurado():
    """Modelo usado como juiz: variável MODELO_JUIZ ou o padrão."""
    return os.getenv("MODELO_JUIZ", "").strip() or JUIZ_PADRAO


def montar_prompt_juiz(pergunta, referencia, resposta):
    return (
        PROMPT_JUIZ
        .replace("<<PERGUNTA>>", pergunta)
        .replace("<<REFERENCIA>>", referencia)
        .replace("<<RESPOSTA>>", resposta or "(resposta vazia)")
    )


def interpretar_veredito(texto):
    """Extrai {aprovado, justificativa} do texto do juiz. Levanta ValueError se não conseguir."""
    if not texto or not texto.strip():
        raise ValueError("Juiz devolveu texto vazio")

    trecho = texto.strip()
    encontrado = re.search(r"\{.*\}", trecho, re.DOTALL)
    if encontrado:
        try:
            dados = json.loads(encontrado.group(0))
            aprovado = dados.get("aprovado")
            if isinstance(aprovado, str):
                aprovado = aprovado.strip().lower() in ("true", "sim", "aprovado", "aprovada")
            if isinstance(aprovado, bool):
                return {
                    "aprovado": aprovado,
                    "justificativa": str(dados.get("justificativa", "")).strip(),
                }
        except json.JSONDecodeError:
            pass

    # Recurso para JSON malformado: procura "aprovado": true/false no texto.
    chave = re.search(r'"?aprovado"?\s*:\s*(true|false)', trecho, re.IGNORECASE)
    if chave:
        return {"aprovado": chave.group(1).lower() == "true", "justificativa": ""}

    raise ValueError(f"Veredito do juiz em formato inesperado: {trecho[:120]!r}")


def julgar(pergunta, referencia, resposta, modelo_juiz=None, cliente=None):
    """Pede o veredito ao juiz. Em caso de falha de formato, aprovado_juiz fica None."""
    modelo_juiz = modelo_juiz or modelo_juiz_configurado()
    mensagens = [{"role": "user", "content": montar_prompt_juiz(pergunta, referencia, resposta)}]

    # O prompt do juiz é curto: 2048 tokens bastam e economizam memória.
    saida = chamar_modelo(modelo_juiz, mensagens, cliente=cliente, formato="json", contexto=2048)

    try:
        veredito = interpretar_veredito(saida["texto"])
        aprovado, justificativa = veredito["aprovado"], veredito["justificativa"]
    except ValueError as erro:
        aprovado, justificativa = None, f"ERRO_FORMATO: {erro}"

    return {
        "aprovado_juiz": aprovado,
        "justificativa_juiz": justificativa,
        "tempo_juiz": saida["tempo"],
        "tokens_juiz": saida["tokens_entrada"] + saida["tokens_saida"],
    }

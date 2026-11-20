"""Comunicação com os modelos via Ollama (local, custo zero)."""

import os
import time

import ollama

MODELOS_PADRAO = [
    "gemma3:4b",
    "llama3.2:3b",
    "qwen2.5:3b",
]

# Opções fixas para que as execuções sejam reprodutíveis.
OPCOES_GERACAO = {"temperature": 0, "seed": 42}


def modelos_configurados():
    """Modelos avaliados: variável MODELOS_AVALIADOS (separada por vírgula) ou o padrão."""
    valor = os.getenv("MODELOS_AVALIADOS", "")
    modelos = [m.strip() for m in valor.split(",") if m.strip()]
    return modelos or list(MODELOS_PADRAO)


def criar_cliente():
    """Cliente Ollama. O endereço vem da variável OLLAMA_HOST (padrão: localhost:11434)."""
    return ollama.Client()


def modelos_instalados(cliente=None):
    """Nomes dos modelos instalados no Ollama."""
    cliente = cliente or criar_cliente()
    try:
        return [modelo.model for modelo in cliente.list().models]
    except Exception as erro:
        raise RuntimeError(f"Não foi possível acessar o Ollama: {erro}") from erro


def listar_modelos(cliente=None):
    """Modelos configurados que estão instalados no Ollama."""
    instalados = modelos_instalados(cliente)
    return [nome for nome in modelos_configurados() if nome in instalados]


def liberar_modelo(modelo, cliente=None):
    """Descarrega o modelo da memória (keep_alive=0). Falhas são ignoradas."""
    cliente = cliente or criar_cliente()
    try:
        cliente.generate(model=modelo, prompt="", keep_alive=0)
    except Exception:
        pass


def chamar_modelo(modelo, mensagens, cliente=None, formato=None, contexto=None):
    """Chama o modelo e devolve texto, tempo e tokens.

    contexto: tamanho da janela (num_ctx). Menor = menos memória.
    """
    cliente = cliente or criar_cliente()
    opcoes = dict(OPCOES_GERACAO)
    if contexto:
        opcoes["num_ctx"] = contexto

    inicio = time.perf_counter()
    resposta = cliente.chat(
        model=modelo,
        messages=mensagens,
        options=opcoes,
        format=formato,
    )
    tempo = time.perf_counter() - inicio

    return {
        "texto": resposta.message.content,
        "tempo": round(tempo, 3),
        "tokens_entrada": resposta.prompt_eval_count or 0,
        "tokens_saida": resposta.eval_count or 0,
    }


def gerar_resposta(modelo, pergunta, prompt_sistema=None, cliente=None, permitidos=None):
    """Envia uma pergunta a um modelo avaliado e mede tempo e tokens."""
    permitidos = permitidos if permitidos is not None else modelos_configurados()
    if modelo not in permitidos:
        raise ValueError(f"Modelo não permitido: {modelo}")

    mensagens = []
    if prompt_sistema:
        mensagens.append({"role": "system", "content": prompt_sistema})
    mensagens.append({"role": "user", "content": pergunta})

    saida = chamar_modelo(modelo, mensagens, cliente=cliente)

    return {
        "modelo": modelo,
        "pergunta": pergunta,
        "resposta": saida["texto"],
        "tempo_resposta": saida["tempo"],
        "tokens_entrada": saida["tokens_entrada"],
        "tokens_saida": saida["tokens_saida"],
    }

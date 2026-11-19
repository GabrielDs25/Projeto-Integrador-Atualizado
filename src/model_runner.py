
import time
import ollama


MODELOS = [
    "gemma3:4b",
    "llama3.2:3b",
    "qwen2.5:3b",
]


def listar_modelos():
    """Retorna os modelos disponíveis no Ollama."""
    try:
        modelos_instalados = ollama.list()
        nomes = [
            modelo.model
            for modelo in modelos_instalados.models
        ]
        return [nome for nome in MODELOS if nome in nomes]
    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível acessar o Ollama: {erro}"
        ) from erro


def gerar_resposta(modelo, pergunta):
    """Envia uma pergunta ao modelo e mede o tempo de resposta."""
    if modelo not in MODELOS:
        raise ValueError(f"Modelo não permitido: {modelo}")

    inicio = time.perf_counter()

    resposta = ollama.chat(
        model=modelo,
        messages=[
            {
                "role": "user",
                "content": pergunta,
            }
        ],
    )

    tempo = time.perf_counter() - inicio

    return {
        "modelo": modelo,
        "pergunta": pergunta,
        "resposta": resposta.message.content,
        "tempo_resposta": round(tempo, 3),
        "tokens_entrada": resposta.prompt_eval_count or 0,
        "tokens_saida": resposta.eval_count or 0,
    }

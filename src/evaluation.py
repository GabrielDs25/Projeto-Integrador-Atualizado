
def accuracy_rate(resultados):
    """Calcula a porcentagem de respostas aprovadas."""
    if not resultados:
        return 0.0

    aprovados = sum(
        1 for resultado in resultados
        if resultado.get("aprovado") is True
    )

    return round((aprovados / len(resultados)) * 100, 2)


def average_response_time(resultados):
    """Calcula o tempo médio de resposta em segundos."""
    if not resultados:
        return 0.0

    tempos = [
        resultado["tempo_resposta"]
        for resultado in resultados
        if resultado.get("tempo_resposta") is not None
    ]

    if not tempos:
        return 0.0

    return round(sum(tempos) / len(tempos), 3)


def average_tokens(resultados):
    """Calcula a média de tokens utilizados por resposta."""
    if not resultados:
        return 0.0

    totais = [
        resultado.get("tokens_entrada", 0)
        + resultado.get("tokens_saida", 0)
        for resultado in resultados
    ]

    return round(sum(totais) / len(totais), 2)


def calculate_metrics(resultados):
    """Retorna as principais métricas de uma avaliação."""
    return {
        "total": len(resultados),
        "taxa_acerto": accuracy_rate(resultados),
        "tempo_medio": average_response_time(resultados),
        "media_tokens": average_tokens(resultados),
    }

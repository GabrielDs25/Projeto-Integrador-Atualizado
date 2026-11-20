"""Métricas: taxa de acerto, concordância (kappa de Cohen) e detecção de regressão."""

CAMPOS_AVALIADOR = {
    "baseline": "aprovado_baseline",
    "juiz": "aprovado_juiz",
    "humano": "aprovado_humano",
}


def accuracy_rate(resultados, campo="aprovado_juiz"):
    """Percentual de aprovados entre os resultados que têm nota no campo."""
    avaliados = [r for r in resultados if r.get(campo) is not None]
    if not avaliados:
        return None
    aprovados = sum(1 for r in avaliados if r[campo] is True)
    return round(aprovados / len(avaliados) * 100, 2)


def average_response_time(resultados):
    """Tempo médio de resposta em segundos."""
    tempos = [r["tempo_resposta"] for r in resultados if r.get("tempo_resposta") is not None]
    if not tempos:
        return 0.0
    return round(sum(tempos) / len(tempos), 3)


def average_tokens(resultados):
    """Média de tokens (entrada + saída) por resposta."""
    if not resultados:
        return 0.0
    totais = [(r.get("tokens_entrada") or 0) + (r.get("tokens_saida") or 0) for r in resultados]
    return round(sum(totais) / len(totais), 2)


def calculate_metrics(resultados):
    """Métricas principais de uma bateria de testes."""
    return {
        "total": len(resultados),
        "taxa_acerto_juiz": accuracy_rate(resultados, "aprovado_juiz"),
        "taxa_acerto_baseline": accuracy_rate(resultados, "aprovado_baseline"),
        "taxa_acerto_humano": accuracy_rate(resultados, "aprovado_humano"),
        "avaliados_humano": sum(1 for r in resultados if r.get("aprovado_humano") is not None),
        "tempo_medio": average_response_time(resultados),
        "tempo_total": round(
            sum((r.get("tempo_resposta") or 0) + (r.get("tempo_juiz") or 0) for r in resultados), 2
        ),
        "media_tokens": average_tokens(resultados),
        "tokens_total": sum(
            (r.get("tokens_entrada") or 0) + (r.get("tokens_saida") or 0) + (r.get("tokens_juiz") or 0)
            for r in resultados
        ),
        "erros": sum(1 for r in resultados if r.get("erro")),
    }


def cohen_kappa(avaliacoes_a, avaliacoes_b):
    """Kappa de Cohen para duas listas de rótulos (mesmo tamanho).

    kappa = (po - pe) / (1 - pe), em que po é o acordo observado e pe o acordo
    esperado ao acaso. Retorna None se não houver dados; 1.0 se ambos os
    avaliadores usaram um único rótulo idêntico (pe = 1).
    """
    if len(avaliacoes_a) != len(avaliacoes_b):
        raise ValueError("As listas de avaliações precisam ter o mesmo tamanho.")
    total = len(avaliacoes_a)
    if total == 0:
        return None

    po = sum(1 for a, b in zip(avaliacoes_a, avaliacoes_b, strict=False) if a == b) / total
    rotulos = set(avaliacoes_a) | set(avaliacoes_b)
    pe = sum(
        (avaliacoes_a.count(rotulo) / total) * (avaliacoes_b.count(rotulo) / total)
        for rotulo in rotulos
    )
    if pe == 1:
        return 1.0
    return round((po - pe) / (1 - pe), 4)


def concordancia(resultados, campo_avaliador="aprovado_juiz", campo_referencia="aprovado_humano"):
    """Compara um avaliador automático com a referência humana.

    Usa apenas os resultados avaliados pelos dois. A matriz considera a
    referência como verdade: falso_positivo = avaliador aprovou algo que o
    humano reprovou.
    """
    pares = [
        (r[campo_avaliador], r[campo_referencia], r)
        for r in resultados
        if r.get(campo_avaliador) is not None and r.get(campo_referencia) is not None
    ]
    a = [p[0] for p in pares]
    b = [p[1] for p in pares]

    matriz = {
        "verdadeiro_positivo": sum(1 for x, y in zip(a, b, strict=False) if x and y),
        "verdadeiro_negativo": sum(1 for x, y in zip(a, b, strict=False) if not x and not y),
        "falso_positivo": sum(1 for x, y in zip(a, b, strict=False) if x and not y),
        "falso_negativo": sum(1 for x, y in zip(a, b, strict=False) if not x and y),
    }
    n = len(pares)
    return {
        "n": n,
        "acordo_percentual": round(sum(1 for x, y in zip(a, b, strict=False) if x == y) / n * 100, 2) if n else None,
        "kappa": cohen_kappa(a, b),
        "matriz": matriz,
        "divergencias": [p[2] for p in pares if p[0] != p[1]],
    }


def interpretar_kappa(kappa):
    """Faixas de Landis e Koch (1977)."""
    if kappa is None:
        return "sem dados"
    if kappa < 0:
        return "pior que o acaso"
    faixas = [(0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"), (0.80, "substancial")]
    for limite, nome in faixas:
        if kappa <= limite:
            return nome
    return "quase perfeita"


def detectar_regressao(resultados_base, resultados_nova, campo="aprovado_juiz", limiar=5.0):
    """Compara duas baterias e acusa regressão se a taxa cair mais que o limiar (em pontos %).

    Também lista os casos que passavam na base e falham na nova versão.
    """
    taxa_base = accuracy_rate(resultados_base, campo)
    taxa_nova = accuracy_rate(resultados_nova, campo)
    if taxa_base is None or taxa_nova is None:
        raise ValueError(f"As duas execuções precisam ter notas no campo {campo}.")

    base_por_caso = {
        (r.get("caso_id"), r["modelo"]): r[campo]
        for r in resultados_base
        if r.get("caso_id") and r.get(campo) is not None
    }
    casos_que_pioraram = sorted(
        r["caso_id"]
        for r in resultados_nova
        if r.get(campo) is False and base_por_caso.get((r.get("caso_id"), r["modelo"])) is True
    )

    delta = round(taxa_nova - taxa_base, 2)
    return {
        "campo": campo,
        "taxa_base": taxa_base,
        "taxa_nova": taxa_nova,
        "delta": delta,
        "limiar": limiar,
        "regressao": delta < -limiar,
        "casos_que_pioraram": casos_que_pioraram,
    }

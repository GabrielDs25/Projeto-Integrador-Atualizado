import pytest

from src.evaluation import (
    accuracy_rate,
    calculate_metrics,
    cohen_kappa,
    concordancia,
    detectar_regressao,
    interpretar_kappa,
)


def test_accuracy_ignora_nao_avaliados():
    resultados = [{"aprovado_juiz": True}, {"aprovado_juiz": False}, {"aprovado_juiz": None}]
    assert accuracy_rate(resultados) == 50.0
    assert accuracy_rate([]) is None


def test_kappa_exemplo_conhecido():
    # 50 itens: 20 ambos sim, 5 só A sim, 10 só B sim, 15 ambos não.
    # po = 0.70; pe = 0.5*0.6 + 0.5*0.4 = 0.50; kappa = 0.4
    a = [True] * 20 + [True] * 5 + [False] * 10 + [False] * 15
    b = [True] * 20 + [False] * 5 + [True] * 10 + [False] * 15
    assert cohen_kappa(a, b) == pytest.approx(0.4)


def test_kappa_acordo_perfeito_e_casos_limite():
    assert cohen_kappa([True, False], [True, False]) == 1.0
    assert cohen_kappa([True, True], [True, True]) == 1.0
    assert cohen_kappa([], []) is None
    with pytest.raises(ValueError):
        cohen_kappa([True], [])


def test_concordancia_matriz_e_divergencias():
    resultados = [
        {"aprovado_juiz": True, "aprovado_humano": True},
        {"aprovado_juiz": True, "aprovado_humano": False},
        {"aprovado_juiz": False, "aprovado_humano": True},
        {"aprovado_juiz": False, "aprovado_humano": False},
        {"aprovado_juiz": True, "aprovado_humano": None},
    ]
    c = concordancia(resultados)
    assert c["n"] == 4
    assert c["acordo_percentual"] == 50.0
    assert c["matriz"] == {
        "verdadeiro_positivo": 1, "verdadeiro_negativo": 1,
        "falso_positivo": 1, "falso_negativo": 1,
    }
    assert len(c["divergencias"]) == 2


def test_regressao_detectada_e_casos_listados():
    base = [{"caso_id": f"C{i}", "modelo": "m", "aprovado_juiz": True} for i in range(10)]
    nova = [{"caso_id": f"C{i}", "modelo": "m", "aprovado_juiz": i < 6} for i in range(10)]
    r = detectar_regressao(base, nova, limiar=5)
    assert r["delta"] == -40.0
    assert r["regressao"] is True
    assert r["casos_que_pioraram"] == ["C6", "C7", "C8", "C9"]


def test_sem_regressao_dentro_do_limiar():
    base = [{"caso_id": f"C{i}", "modelo": "m", "aprovado_juiz": i < 9} for i in range(10)]
    assert detectar_regressao(base, base)["regressao"] is False


def test_regressao_exige_notas():
    with pytest.raises(ValueError):
        detectar_regressao([{"aprovado_juiz": None}], [{"aprovado_juiz": True}])


def test_metricas_somam_tokens_e_tempo():
    comum = {"tempo_juiz": 0.5, "tokens_entrada": 10, "tokens_saida": 5, "tokens_juiz": 3}
    resultados = [
        {**comum, "tempo_resposta": 1.0, "aprovado_juiz": True},
        {**comum, "tempo_resposta": 3.0, "aprovado_juiz": False, "erro": "x"},
    ]
    m = calculate_metrics(resultados)
    assert m["tempo_medio"] == 2.0
    assert m["tempo_total"] == 5.0
    assert m["tokens_total"] == 36
    assert m["erros"] == 1
    assert m["taxa_acerto_juiz"] == 50.0


def test_interpretar_kappa():
    assert interpretar_kappa(None) == "sem dados"
    assert interpretar_kappa(-0.1) == "pior que o acaso"
    assert interpretar_kappa(0.5) == "moderada"
    assert interpretar_kappa(0.9) == "quase perfeita"

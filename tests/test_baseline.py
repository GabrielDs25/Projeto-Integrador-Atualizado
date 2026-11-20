from src.baseline import avaliar_baseline, normalizar


def test_normalizar_remove_acentos_e_maiusculas():
    assert normalizar("  Programação   DINÂMICA ") == "programacao dinamica"


def test_aprova_quando_contem_palavra_chave():
    assert avaliar_baseline("O resultado é 8.", ["8", "oito"])
    assert avaliar_baseline("Dá OITO.", ["8", "oito"])


def test_nao_aceita_palavra_dentro_de_outra():
    assert not avaliar_baseline("O resultado é 18.", ["8"])
    assert not avaliar_baseline("Use a função length", ["len"])


def test_resposta_vazia_reprova():
    assert not avaliar_baseline("", ["8"])
    assert not avaliar_baseline(None, ["8"])


def test_limitacao_conhecida_negacao_passa():
    # O baseline não entende negação: este é um falso positivo esperado
    # e um dos motivos para usar o LLM juiz.
    assert avaliar_baseline("Não é 8.", ["8"])

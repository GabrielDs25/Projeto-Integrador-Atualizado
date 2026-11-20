import pytest

from src.judge import interpretar_veredito, julgar, montar_prompt_juiz


def test_interpreta_json_valido():
    v = interpretar_veredito('{"aprovado": true, "justificativa": "Correto."}')
    assert v == {"aprovado": True, "justificativa": "Correto."}


def test_interpreta_json_cercado_de_texto():
    v = interpretar_veredito('Aqui está: {"aprovado": false, "justificativa": "Errado"} fim')
    assert v["aprovado"] is False


def test_interpreta_aprovado_como_texto():
    assert interpretar_veredito('{"aprovado": "sim"}')["aprovado"] is True


def test_recupera_json_malformado():
    assert interpretar_veredito('{"aprovado": false, "justificativa": "sem fechar')["aprovado"] is False


@pytest.mark.parametrize("texto", ["", "não sei", '{"nota": 5}'])
def test_formato_inesperado_levanta_erro(texto):
    with pytest.raises(ValueError):
        interpretar_veredito(texto)


def test_prompt_contem_campos():
    prompt = montar_prompt_juiz("P?", "REF", "RESP")
    assert "P?" in prompt and "REF" in prompt and "RESP" in prompt


def test_julgar_usa_formato_json(cliente_falso):
    cliente = cliente_falso({"juiz": '{"aprovado": true, "justificativa": "ok"}'})
    r = julgar("P?", "REF", "RESP", modelo_juiz="juiz", cliente=cliente)
    assert r["aprovado_juiz"] is True
    assert r["tokens_juiz"] == 15
    assert cliente.chamadas[0]["format"] == "json"


def test_julgar_com_resposta_invalida_marca_none(cliente_falso):
    cliente = cliente_falso({"juiz": "talvez"})
    r = julgar("P?", "REF", "RESP", modelo_juiz="juiz", cliente=cliente)
    assert r["aprovado_juiz"] is None
    assert r["justificativa_juiz"].startswith("ERRO_FORMATO")

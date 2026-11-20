import pytest

from src.model_runner import gerar_resposta, listar_modelos, modelos_configurados


def test_modelos_configurados_por_variavel(monkeypatch):
    monkeypatch.setenv("MODELOS_AVALIADOS", "a:1, b:2")
    assert modelos_configurados() == ["a:1", "b:2"]
    monkeypatch.delenv("MODELOS_AVALIADOS")
    assert len(modelos_configurados()) == 3


def test_modelo_nao_permitido():
    with pytest.raises(ValueError):
        gerar_resposta("desconhecido", "oi", permitidos=["a"])


def test_gerar_resposta_mede_tokens(cliente_falso):
    r = gerar_resposta("a", "oi", cliente=cliente_falso({"a": "olá"}), permitidos=["a"])
    assert r["resposta"] == "olá"
    assert r["tokens_entrada"] == 10
    assert r["tokens_saida"] == 5


def test_listar_apenas_instalados(monkeypatch, cliente_falso):
    monkeypatch.setenv("MODELOS_AVALIADOS", "a,b")
    assert listar_modelos(cliente_falso(instalados=["b", "c"])) == ["b"]


def test_ollama_fora_do_ar_gera_runtime_error():
    class Quebrado:
        def list(self):
            raise ConnectionError("recusado")

    with pytest.raises(RuntimeError, match="Ollama"):
        listar_modelos(Quebrado())

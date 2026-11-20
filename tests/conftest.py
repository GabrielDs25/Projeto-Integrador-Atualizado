from types import SimpleNamespace

import pytest


class ClienteFalso:
    """Imita ollama.Client: devolve respostas programadas por modelo."""

    def __init__(self, respostas=None, instalados=None, falhar=None):
        self.respostas = respostas or {}
        self.instalados = instalados or []
        self.falhar = set(falhar or [])
        self.chamadas = []

    def chat(self, model, messages, options=None, format=None):
        self.chamadas.append({"model": model, "messages": messages, "format": format})
        if model in self.falhar:
            raise ConnectionError(f"{model} fora do ar")
        conteudo = self.respostas.get(model, "")
        if callable(conteudo):
            conteudo = conteudo(messages)
        return SimpleNamespace(
            message=SimpleNamespace(content=conteudo),
            prompt_eval_count=10,
            eval_count=5,
        )

    def generate(self, model, prompt="", keep_alive=None):
        self.chamadas.append({"model": model, "liberar": keep_alive == 0})
        return SimpleNamespace(response="")

    def list(self):
        return SimpleNamespace(models=[SimpleNamespace(model=m) for m in self.instalados])


@pytest.fixture
def cliente_falso():
    return ClienteFalso


@pytest.fixture
def db(tmp_path):
    from src.results_store import initialize_database

    caminho = tmp_path / "teste.db"
    initialize_database(caminho)
    return caminho

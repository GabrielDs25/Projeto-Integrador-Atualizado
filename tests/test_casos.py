import json

import pytest

from src.baseline import avaliar_baseline
from src.casos import carregar_casos, carregar_prompt, validar_casos


def test_dataset_tem_100_casos_unicos_e_split_30_70():
    casos = carregar_casos()
    assert len(casos) == 100
    assert len({c["id"] for c in casos}) == 100
    assert len(carregar_casos(split="calibracao")) == 30
    assert len(carregar_casos(split="teste")) == 70


def test_baseline_aprova_a_propria_referencia():
    # Coerência do dataset: a resposta de referência passa no baseline.
    falhas = [
        c["id"] for c in carregar_casos()
        if not avaliar_baseline(c["resposta_referencia"], c["palavras_chave"])
    ]
    assert falhas == []


def test_limite_e_split_invalido():
    assert len(carregar_casos(limite=5)) == 5
    with pytest.raises(ValueError):
        carregar_casos(split="treino")


def test_validacao_detecta_id_repetido():
    caso = {"id": "X", "split": "teste", "pergunta": "p", "resposta_referencia": "r", "palavras_chave": ["r"]}
    with pytest.raises(ValueError, match="repetido"):
        validar_casos([caso, dict(caso)])


def test_validacao_detecta_campo_faltando(tmp_path):
    arquivo = tmp_path / "casos.json"
    arquivo.write_text(json.dumps([{"id": "X", "split": "teste"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="sem os campos"):
        carregar_casos(arquivo)


def test_prompts_existem():
    assert carregar_prompt("v1")
    assert carregar_prompt("v2_piorado")
    with pytest.raises(FileNotFoundError):
        carregar_prompt("nao_existe")

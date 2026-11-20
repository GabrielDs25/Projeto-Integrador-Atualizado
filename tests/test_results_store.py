import sqlite3

import pytest

from src.results_store import (
    create_run,
    initialize_database,
    listar_execucoes,
    listar_resultados,
    registrar_avaliacao_humana,
    save_result,
)


def test_salvar_e_listar(db):
    eid = create_run("teste", db_path=db, origem="bateria", modelo="m", versao_prompt="v1")
    rid = save_result(
        eid,
        {"modelo": "m", "pergunta": "p", "resposta": "r", "aprovado_juiz": True, "aprovado_baseline": False},
        db_path=db,
    )
    [r] = listar_resultados(eid, db_path=db)
    assert r["id"] == rid
    assert r["aprovado_juiz"] is True
    assert r["aprovado_baseline"] is False
    assert r["aprovado_humano"] is None
    [e] = listar_execucoes(origem="bateria", db_path=db)
    assert e["total_resultados"] == 1


def test_avaliacao_humana(db):
    eid = create_run(db_path=db)
    rid = save_result(eid, {"modelo": "m", "pergunta": "p"}, db_path=db)
    registrar_avaliacao_humana(rid, False, "Ana", db_path=db)
    [r] = listar_resultados(eid, db_path=db)
    assert r["aprovado_humano"] is False
    assert r["avaliador_humano"] == "Ana"
    with pytest.raises(ValueError):
        registrar_avaliacao_humana(999, True, db_path=db)


def test_campo_desconhecido_e_chave_estrangeira(db):
    with pytest.raises(ValueError):
        create_run(db_path=db, campo_inexistente=1)
    with pytest.raises(sqlite3.IntegrityError):
        save_result(12345, {"modelo": "m", "pergunta": "p"}, db_path=db)


def test_migra_banco_da_versao_antiga(tmp_path):
    caminho = tmp_path / "antigo.db"
    conexao = sqlite3.connect(caminho)
    conexao.execute(
        "CREATE TABLE execucoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT, descricao TEXT)"
    )
    conexao.execute(
        "CREATE TABLE resultados (id INTEGER PRIMARY KEY AUTOINCREMENT, execucao_id INTEGER, "
        "modelo TEXT, pergunta TEXT, resposta TEXT, aprovado INTEGER)"
    )
    conexao.commit()
    conexao.close()

    initialize_database(caminho)
    eid = create_run(db_path=caminho, versao_prompt="v1")
    save_result(eid, {"modelo": "m", "pergunta": "p", "aprovado_juiz": True}, db_path=caminho)
    assert listar_resultados(eid, db_path=caminho)[0]["aprovado_juiz"] is True

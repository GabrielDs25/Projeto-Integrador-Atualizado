from src.results_store import listar_execucoes, listar_resultados
from src.runner import executar_bateria

CASOS = [
    {"id": "C001", "categoria": "python", "pergunta": "2**3?", "resposta_referencia": "8", "palavras_chave": ["8"]},
    {"id": "C002", "categoria": "python", "pergunta": "len?", "resposta_referencia": "len", "palavras_chave": ["len"]},
]


def juiz_simples(messages):
    texto = messages[0]["content"]
    correto = "Resposta do modelo avaliado: 8\n" in texto and "Pergunta: 2**3?" in texto
    return '{"aprovado": ' + ("true" if correto else "false") + ', "justificativa": "teste"}'


def test_bateria_completa(db, cliente_falso):
    cliente = cliente_falso({"modelo-a": "8", "juiz": juiz_simples})
    eid = executar_bateria(
        CASOS, "modelo-a", "v1", "seja direto", modelo_juiz="juiz",
        cliente=cliente, db_path=db, permitidos=["modelo-a"],
    )
    resultados = listar_resultados(eid, db_path=db)
    assert [r["caso_id"] for r in resultados] == ["C001", "C002"]
    assert resultados[0]["aprovado_baseline"] is True
    assert resultados[0]["aprovado_juiz"] is True
    assert resultados[1]["aprovado_baseline"] is False
    assert resultados[1]["aprovado_juiz"] is False

    [e] = listar_execucoes(db_path=db)
    assert e["versao_prompt"] == "v1"
    assert e["modelo_juiz"] == "juiz"
    # O prompt de sistema da versão é enviado ao modelo avaliado.
    assert cliente.chamadas[0]["messages"][0] == {"role": "system", "content": "seja direto"}
    # Ordem: 2 respostas, descarrega o modelo avaliado, 2 julgamentos.
    assert [c["model"] for c in cliente.chamadas] == ["modelo-a", "modelo-a", "modelo-a", "juiz", "juiz"]
    assert cliente.chamadas[2].get("liberar") is True


def test_falha_do_modelo_e_registrada_sem_derrubar(db, cliente_falso):
    cliente = cliente_falso(falhar=["modelo-a"])
    eid = executar_bateria(
        CASOS, "modelo-a", "v1", "", modelo_juiz="juiz",
        cliente=cliente, db_path=db, permitidos=["modelo-a"],
    )
    resultados = listar_resultados(eid, db_path=db)
    assert len(resultados) == 2
    assert all(r["erro"].startswith("modelo:") for r in resultados)


def test_falha_do_juiz_e_registrada(db, cliente_falso):
    cliente = cliente_falso({"modelo-a": "8"}, falhar=["juiz"])
    eid = executar_bateria(
        CASOS[:1], "modelo-a", "v1", "", modelo_juiz="juiz",
        cliente=cliente, db_path=db, permitidos=["modelo-a"],
    )
    [r] = listar_resultados(eid, db_path=db)
    assert r["aprovado_baseline"] is True
    assert r["aprovado_juiz"] is None
    assert r["erro"].startswith("juiz:")


def test_sem_juiz(db, cliente_falso):
    cliente = cliente_falso({"modelo-a": "8"})
    eid = executar_bateria(
        CASOS, "modelo-a", "v1", "", usar_juiz=False,
        cliente=cliente, db_path=db, permitidos=["modelo-a"],
    )
    assert all(r["aprovado_juiz"] is None for r in listar_resultados(eid, db_path=db))
    assert len(cliente.chamadas) == 2

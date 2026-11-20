import csv

from src import cli
from src.results_store import create_run, listar_resultados, save_result


def _preparar(db, monkeypatch, acertos_nova):
    monkeypatch.setattr("src.results_store.DATABASE_PATH", db)
    base = create_run(origem="bateria", modelo="m", versao_prompt="v1")
    nova = create_run(origem="bateria", modelo="m", versao_prompt="v2")
    for i in range(10):
        save_result(base, {"caso_id": f"C{i}", "modelo": "m", "pergunta": "p", "aprovado_juiz": True})
        save_result(nova, {"caso_id": f"C{i}", "modelo": "m", "pergunta": "p", "aprovado_juiz": i < acertos_nova})
    return base, nova


def test_comparar_retorna_1_em_regressao(db, monkeypatch, capsys):
    base, nova = _preparar(db, monkeypatch, acertos_nova=5)
    assert cli.main(["comparar", str(base), str(nova)]) == 1
    assert "REGRESSÃO DETECTADA" in capsys.readouterr().out


def test_comparar_retorna_0_sem_regressao(db, monkeypatch):
    base, nova = _preparar(db, monkeypatch, acertos_nova=10)
    assert cli.main(["comparar", str(base), str(nova)]) == 0


def test_execucao_inexistente(db, monkeypatch):
    monkeypatch.setattr("src.results_store.DATABASE_PATH", db)
    assert cli.main(["comparar", "98", "99"]) == 2


def test_exportar_importar_humano_e_concordancia(db, monkeypatch, tmp_path):
    base, _ = _preparar(db, monkeypatch, acertos_nova=10)
    assert cli.main(["exportar", str(base), "--saida", str(tmp_path)]) == 0
    assert (tmp_path / "metricas.json").exists()

    caminho = tmp_path / f"execucao_{base}.csv"
    with open(caminho, encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    for linha in linhas:
        linha["aprovado_humano"] = "sim"
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)

    assert cli.main(["importar-humano", str(caminho), "--avaliador", "Ana"]) == 0
    assert all(r["aprovado_humano"] is True for r in listar_resultados(base))
    assert cli.main(["concordancia", str(base), "--detalhes"]) == 0

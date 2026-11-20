from PIL import Image

from src.erros import classificar, coletar_erros, exportar_erros

EXECUCAO = {"id": 1, "data_hora": "2026-11-19 10:00:00", "versao_prompt": "v1", "modelo_juiz": "juiz"}


def _r(**campos):
    base = {"id": 1, "caso_id": "C001", "modelo": "m", "pergunta": "2**3?", "resposta_referencia": "8",
            "resposta": "8", "aprovado_baseline": True, "aprovado_juiz": True, "aprovado_humano": None}
    return {**base, **campos}


def test_classificacao():
    assert classificar(_r()) == []
    assert classificar(_r(erro="modelo: fora do ar")) == ["falha_execucao"]
    assert classificar(_r(aprovado_juiz=False, aprovado_baseline=False)) == ["modelo_errou"]
    # Humano reprovou, juiz e baseline aprovaram.
    assert classificar(_r(aprovado_humano=False)) == ["modelo_errou", "juiz_errou", "baseline_errou"]
    # Humano aprovou, só o baseline reprovou.
    assert classificar(_r(aprovado_humano=True, aprovado_baseline=False)) == ["baseline_errou"]
    # Sem nota humana e juiz x baseline em desacordo: não culpa ninguém, pede revisão.
    assert classificar(_r(aprovado_baseline=False)) == ["revisar"]
    assert classificar(_r(aprovado_juiz=False)) == ["revisar"]


def test_coletar_filtra_por_tipo():
    resultados = [_r(), _r(id=2, erro="x"), _r(id=3, aprovado_juiz=False, aprovado_baseline=False)]
    assert len(coletar_erros(resultados)) == 2
    assert [e["id"] for e in coletar_erros(resultados, tipos=["falha_execucao"])] == [2]


def test_exportar_gera_png_indice_e_preserva_causas(tmp_path):
    resposta_longa = "palavra " * 200 + "x" * 300
    resultados = [_r(), _r(id=2, caso_id="C002", resposta=resposta_longa, aprovado_juiz=False,
                         aprovado_baseline=False, justificativa_juiz="Resposta vaga.")]
    erros = exportar_erros([(EXECUCAO, resultados)], tmp_path)
    assert len(erros) == 1

    png = tmp_path / erros[0]["arquivo"]
    with Image.open(png) as img:
        assert img.width == 1200 and img.height > 400
    indice = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert erros[0]["arquivo"] in indice and "_a preencher_" in indice
    assert (tmp_path / "erros.json").exists()

    # O grupo preenche a causa; ao regenerar, ela é mantida.
    (tmp_path / "README.md").write_text(
        indice.replace("_a preencher_ |", "Prompt pede no máximo duas frases |"), encoding="utf-8"
    )
    exportar_erros([(EXECUCAO, resultados)], tmp_path)
    assert "Prompt pede no máximo duas frases" in (tmp_path / "README.md").read_text(encoding="utf-8")

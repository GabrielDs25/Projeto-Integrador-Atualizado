"""Painel Streamlit da plataforma de avaliação de LLMs.

Rodar a partir da raiz do projeto:  python -m streamlit run src/app.py
"""

import sys
from pathlib import Path

# Permite "from src..." quando o Streamlit roda o arquivo direto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.evaluation import (  # noqa: E402
    calculate_metrics,
    concordancia,
    detectar_regressao,
    interpretar_kappa,
)
from src.model_runner import gerar_resposta, listar_modelos  # noqa: E402
from src.results_store import (  # noqa: E402
    create_run,
    initialize_database,
    listar_execucoes,
    listar_resultados,
    registrar_avaliacao_humana,
    save_result,
)

st.set_page_config(page_title="Plataforma de avaliação de LLMs", page_icon=":material/science:", layout="wide")
initialize_database()

st.title("Plataforma de avaliação de LLMs")
st.caption("Baterias de teste por versão de prompt, LLM como juiz calibrado contra notas humanas e detecção de regressão.")

VISOES = ["Resultados por versão", "Regressão", "Avaliação humana", "Juiz × humano", "Pergunta livre"]
visao = st.segmented_control("Visão", VISOES, default=VISOES[0], label_visibility="collapsed")

execucoes = listar_execucoes(origem="bateria")
rotulos = {
    e["id"]: f"#{e['id']} · {e['modelo']} · {e['versao_prompt']} · {e['data_hora']}"
    for e in execucoes
}


def exigir_execucoes():
    if not execucoes:
        st.info("Nenhuma bateria registrada. Rode: `python -m src.cli rodar --versao v1`", title="Sem dados")
        st.stop()


def fmt_pct(valor):
    return "-" if valor is None else f"{valor}%"


if visao == "Resultados por versão":
    exigir_execucoes()
    linhas = []
    for e in execucoes:
        m = calculate_metrics(listar_resultados(e["id"]))
        linhas.append({
            "execução": e["id"],
            "data/hora": e["data_hora"],
            "modelo": e["modelo"],
            "versão do prompt": e["versao_prompt"],
            "casos": m["total"],
            "acerto (juiz) %": m["taxa_acerto_juiz"],
            "acerto (baseline) %": m["taxa_acerto_baseline"],
            "acerto (humano) %": m["taxa_acerto_humano"],
            "tempo médio (s)": m["tempo_medio"],
            "tempo total (s)": m["tempo_total"],
            "tokens totais": m["tokens_total"],
            "erros": m["erros"],
        })
    tabela = pd.DataFrame(linhas)

    st.subheader("Taxa de acerto do juiz por modelo e versão")
    grafico = tabela.dropna(subset=["acerto (juiz) %"])
    if not grafico.empty:
        grafico = grafico.groupby(["modelo", "versão do prompt"], as_index=False)["acerto (juiz) %"].last()
        st.bar_chart(grafico, x="modelo", y="acerto (juiz) %", color="versão do prompt", stack=False)

    st.subheader("Todas as execuções")
    st.dataframe(tabela, hide_index=True)

    st.subheader("Detalhes de uma execução")
    escolhida = st.selectbox("Execução", list(rotulos), format_func=rotulos.get)
    detalhes = pd.DataFrame(listar_resultados(escolhida))
    colunas = ["caso_id", "categoria", "pergunta", "resposta_referencia", "resposta",
               "aprovado_baseline", "aprovado_juiz", "justificativa_juiz", "aprovado_humano",
               "tempo_resposta", "erro"]
    st.dataframe(detalhes[[c for c in colunas if c in detalhes]], hide_index=True)

elif visao == "Regressão":
    exigir_execucoes()
    st.write("Compare uma execução de referência com uma nova versão. A plataforma acusa regressão "
             "quando a taxa de acerto cai mais que o limiar.")
    with st.container(horizontal=True, vertical_alignment="bottom"):
        ids = list(rotulos)
        base = st.selectbox("Execução base", ids, index=min(1, len(ids) - 1), format_func=rotulos.get)
        nova = st.selectbox("Execução nova", ids, index=0, format_func=rotulos.get)
        limiar = st.number_input("Limiar (pontos %)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)

    try:
        r = detectar_regressao(listar_resultados(base), listar_resultados(nova), limiar=limiar)
    except ValueError as erro:
        st.warning(str(erro))
        st.stop()

    with st.container(horizontal=True):
        st.metric("Base", fmt_pct(r["taxa_base"]), border=True)
        st.metric("Nova", fmt_pct(r["taxa_nova"]), delta=f"{r['delta']:+} p.p.", border=True)
        st.metric("Casos que pioraram", len(r["casos_que_pioraram"]), border=True)

    if r["regressao"]:
        st.error(f"Queda de {abs(r['delta'])} pontos, acima do limiar de {limiar}.", title="Regressão detectada")
    else:
        st.success("A variação está dentro do limiar.", title="Sem regressão")
    if r["casos_que_pioraram"]:
        st.write("Casos que passavam e passaram a falhar: " + ", ".join(r["casos_que_pioraram"]))

elif visao == "Avaliação humana":
    exigir_execucoes()
    st.write("Avalie as respostas sem ver o veredito do juiz nem do baseline, para não influenciar a nota. "
             "Essas notas são a referência para calibrar o juiz.")
    with st.container(horizontal=True, vertical_alignment="bottom"):
        escolhida = st.selectbox("Execução", list(rotulos), format_func=rotulos.get, key="exec_humano")
        avaliador = st.text_input("Seu nome (avaliador)")

    resultados = listar_resultados(escolhida)
    opcoes = {None: "Pendente", True: "Aprovada", False: "Reprovada"}
    tabela = pd.DataFrame([{
        "id": r["id"],
        "caso": r["caso_id"],
        "pergunta": r["pergunta"],
        "referência": r["resposta_referencia"],
        "resposta do modelo": r["resposta"],
        "nota": opcoes[r["aprovado_humano"]],
    } for r in resultados])

    pendentes = int((tabela["nota"] == "Pendente").sum()) if not tabela.empty else 0
    st.caption(f"{len(tabela) - pendentes} de {len(tabela)} respostas já avaliadas.")

    editada = st.data_editor(
        tabela,
        hide_index=True,
        disabled=["id", "caso", "pergunta", "referência", "resposta do modelo"],
        column_config={
            "id": None,
            "resposta do modelo": st.column_config.TextColumn(width="large"),
            "nota": st.column_config.SelectboxColumn(options=list(opcoes.values()), required=True),
        },
        key=f"editor_{escolhida}",
    )

    if st.button("Salvar avaliações", type="primary", icon=":material/save:"):
        if not avaliador.strip():
            st.warning("Informe o nome do avaliador antes de salvar.")
        else:
            inverso = {v: k for k, v in opcoes.items()}
            alteradas = 0
            for original, nova in zip(tabela.itertuples(), editada.itertuples(), strict=False):
                if original.nota != nova.nota:
                    registrar_avaliacao_humana(int(nova.id), inverso[nova.nota], avaliador.strip())
                    alteradas += 1
            st.success(f"{alteradas} avaliação(ões) salva(s).")

elif visao == "Juiz × humano":
    exigir_execucoes()
    selecionadas = st.multiselect(
        "Execuções consideradas", list(rotulos), default=list(rotulos), format_func=rotulos.get,
    )
    resultados = [r for eid in selecionadas for r in listar_resultados(eid)]

    colunas = st.columns(2)
    avaliadores = [("Juiz LLM", "aprovado_juiz"), ("Baseline (palavra-chave)", "aprovado_baseline")]
    for coluna, (nome, campo) in zip(colunas, avaliadores, strict=True):
        c = concordancia(resultados, campo)
        with coluna.container(border=True):
            st.subheader(f"{nome} × humano")
            if not c["n"]:
                st.info("Ainda não há respostas avaliadas por humanos.")
                continue
            with st.container(horizontal=True):
                st.metric("Casos", c["n"])
                st.metric("Acordo", fmt_pct(c["acordo_percentual"]))
                st.metric("Kappa de Cohen", c["kappa"])
            st.caption(f"Interpretação (Landis e Koch): {interpretar_kappa(c['kappa'])}")
            m = c["matriz"]
            st.dataframe(pd.DataFrame(
                {"humano aprovou": [m["verdadeiro_positivo"], m["falso_negativo"]],
                 "humano reprovou": [m["falso_positivo"], m["verdadeiro_negativo"]]},
                index=[f"{nome} aprovou", f"{nome} reprovou"],
            ))

    divergencias = concordancia(resultados, "aprovado_juiz")["divergencias"]
    if divergencias:
        st.subheader(f"Casos em que o juiz errou ({len(divergencias)})")
        st.dataframe(pd.DataFrame(divergencias)[
            ["caso_id", "modelo", "pergunta", "resposta_referencia", "resposta",
             "aprovado_juiz", "aprovado_humano", "justificativa_juiz"]
        ], hide_index=True)

elif visao == "Pergunta livre":
    st.write("Envie uma pergunta avulsa aos modelos para explorar o comportamento (não entra nas métricas das baterias).")
    try:
        disponiveis = listar_modelos()
    except RuntimeError as erro:
        st.error(str(erro), title="Ollama indisponível")
        st.stop()
    if not disponiveis:
        st.warning("Nenhum dos modelos configurados está instalado no Ollama.")
        st.stop()

    with st.form("pergunta_livre"):
        modelos = st.multiselect("Modelos", disponiveis, default=disponiveis)
        pergunta = st.text_area("Pergunta", placeholder="Exemplo: o que é uma closure em Python?")
        enviar = st.form_submit_button("Perguntar", type="primary")

    if enviar:
        if not pergunta.strip() or not modelos:
            st.warning("Digite uma pergunta e selecione ao menos um modelo.")
        else:
            execucao_id = create_run("pergunta livre", origem="manual")
            for modelo in modelos:
                with st.container(border=True):
                    st.markdown(f"**{modelo}**")
                    try:
                        with st.spinner("Gerando resposta..."):
                            r = gerar_resposta(modelo, pergunta)
                        save_result(execucao_id, r)
                        st.write(r["resposta"])
                        st.caption(f"{r['tempo_resposta']:.2f} s · {r['tokens_entrada'] + r['tokens_saida']} tokens")
                    except Exception as erro:
                        st.error(f"Erro no modelo {modelo}: {erro}")

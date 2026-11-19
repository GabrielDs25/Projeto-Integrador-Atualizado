
import streamlit as st

from src.model_runner import listar_modelos, gerar_resposta
from src.evaluation import calculate_metrics
from src.results_store import (
    initialize_database,
    create_run,
    save_result,
    listar_resultados,
)


st.set_page_config(
    page_title="Plataforma de Avaliação de IAs",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Plataforma de Avaliação de Modelos de IA")
st.write(
    "Compare respostas de diferentes modelos, "
    "avalie a qualidade e acompanhe o desempenho."
)

initialize_database()

if "resultados_atuais" not in st.session_state:
    st.session_state.resultados_atuais = []

if "resultados_salvos" not in st.session_state:
    st.session_state.resultados_salvos = False


# Seleção dos modelos
st.header("1. Configuração da avaliação")

try:
    modelos_disponiveis = listar_modelos()
except Exception as erro:
    st.error(f"Erro ao consultar o Ollama: {erro}")
    st.stop()

if not modelos_disponiveis:
    st.warning("Nenhum dos modelos configurados foi encontrado no Ollama.")
    st.stop()

modelos_selecionados = st.multiselect(
    "Selecione os modelos que deseja comparar:",
    options=modelos_disponiveis,
    default=modelos_disponiveis,
)

pergunta = st.text_area(
    "Digite a pergunta que será enviada aos modelos:",
    placeholder="Exemplo: Explique o que é inteligência artificial.",
)

descricao = st.text_input(
    "Descrição da execução (opcional):"
)


# Executar avaliação
st.header("2. Executar comparação")

if st.button("Executar avaliação", type="primary"):
    if not pergunta.strip():
        st.warning("Digite uma pergunta antes de executar.")
    elif not modelos_selecionados:
        st.warning("Selecione pelo menos um modelo.")
    else:
        resultados = []

        barra = st.progress(0)
        status = st.empty()

        for indice, modelo in enumerate(modelos_selecionados):
            status.write(f"Consultando {modelo}...")

            try:
                resultado = gerar_resposta(modelo, pergunta)
                resultado["aprovado"] = None
                resultados.append(resultado)

            except Exception as erro:
                st.error(f"Erro no modelo {modelo}: {erro}")

            barra.progress((indice + 1) / len(modelos_selecionados))

        st.session_state.resultados_atuais = resultados
        st.session_state.resultados_salvos = False

        status.success("Execução concluída!")


# Exibir respostas e avaliações humanas
resultados_atuais = st.session_state.resultados_atuais

if resultados_atuais:
    st.header("3. Comparação das respostas")

    for indice, resultado in enumerate(resultados_atuais):
        with st.expander(
            f"Modelo: {resultado['modelo']}",
            expanded=True,
        ):
            st.write("**Pergunta:**")
            st.write(resultado["pergunta"])

            st.write("**Resposta:**")
            st.write(resultado["resposta"])

            col1, col2 = st.columns(2)

            col1.metric(
                "Tempo de resposta",
                f"{resultado['tempo_resposta']:.2f} s",
            )

            total_tokens = (
                resultado["tokens_entrada"]
                + resultado["tokens_saida"]
            )

            col2.metric("Total de tokens", total_tokens)

            st.caption(
                f"Tokens de entrada: {resultado['tokens_entrada']} | "
                f"Tokens de saída: {resultado['tokens_saida']}"
            )

            avaliacao = st.selectbox(
                "Avaliação humana da resposta:",
                ["Pendente", "Aprovada", "Reprovada"],
                key=f"avaliacao_{indice}",
                disabled=st.session_state.resultados_salvos,
            )

            if avaliacao == "Aprovada":
                resultado["aprovado"] = True
            elif avaliacao == "Reprovada":
                resultado["aprovado"] = False
            else:
                resultado["aprovado"] = None

    # Salvar resultados
    st.header("4. Salvar avaliação")

    if not st.session_state.resultados_salvos:
        if st.button("Salvar resultados no banco de dados"):
            try:
                execucao_id = create_run(descricao)

                for resultado in resultados_atuais:
                    save_result(execucao_id, resultado)

                st.session_state.resultados_salvos = True
                st.success(
                    f"Resultados salvos! Identificador da execução: "
                    f"{execucao_id}"
                )
                st.rerun()

            except Exception as erro:
                st.error(f"Erro ao salvar os resultados: {erro}")
    else:
        st.success("Esta avaliação já foi salva no banco de dados.")

    # Métricas das respostas avaliadas
    avaliados = [
        resultado
        for resultado in resultados_atuais
        if resultado["aprovado"] is not None
    ]

    if avaliados:
        st.header("5. Métricas da avaliação humana")

        metricas = calculate_metrics(avaliados)

        col1, col2, col3 = st.columns(3)

        col1.metric("Respostas avaliadas", metricas["total"])
        col2.metric("Taxa de aprovação", f"{metricas['taxa_acerto']}%")
        col3.metric("Tempo médio", f"{metricas['tempo_medio']} s")

        st.metric("Média de tokens", metricas["media_tokens"])

    elif st.session_state.resultados_salvos:
        st.info("Ainda não há respostas avaliadas por uma pessoa.")


# Histórico
st.header("6. Histórico de avaliações")

try:
    historico = listar_resultados()

    if historico:
        st.dataframe(
            historico,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhuma avaliação foi salva ainda.")

except Exception as erro:
    st.error(f"Não foi possível carregar o histórico: {erro}")

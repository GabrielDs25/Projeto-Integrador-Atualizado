"""Execução de uma bateria de testes em duas fases.

Fase 1: o modelo avaliado responde a todos os casos (e o baseline avalia).
Fase 2: o juiz avalia todas as respostas.

Separar as fases evita que o Ollama troque o modelo avaliado e o juiz na
memória a cada caso, o que em máquinas sem GPU multiplica o tempo da bateria.
"""

import logging

from src.baseline import avaliar_baseline
from src.judge import VERSAO_PROMPT_JUIZ, julgar, modelo_juiz_configurado
from src.model_runner import gerar_resposta, liberar_modelo
from src.results_store import atualizar_julgamento, create_run, initialize_database, save_result

logger = logging.getLogger("avaliacao")


def responder_caso(caso, modelo, prompt_sistema, cliente=None, permitidos=None):
    """Fase 1 de um caso: resposta do modelo + baseline (sem salvar)."""
    resultado = {
        "caso_id": caso["id"],
        "categoria": caso.get("categoria"),
        "modelo": modelo,
        "pergunta": caso["pergunta"],
        "resposta_referencia": caso["resposta_referencia"],
    }
    try:
        resposta = gerar_resposta(
            modelo, caso["pergunta"], prompt_sistema=prompt_sistema,
            cliente=cliente, permitidos=permitidos,
        )
    except Exception as erro:
        resultado.update({"resposta": "", "erro": f"modelo: {erro}"})
        return resultado

    resultado.update(resposta)
    resultado["aprovado_baseline"] = avaliar_baseline(resposta["resposta"], caso["palavras_chave"])
    return resultado


def julgar_resultado(resultado, modelo_juiz, cliente=None):
    """Fase 2 de um caso: veredito do juiz. Devolve só os campos do julgamento."""
    try:
        return julgar(
            resultado["pergunta"], resultado["resposta_referencia"], resultado["resposta"],
            modelo_juiz=modelo_juiz, cliente=cliente,
        )
    except Exception as erro:
        return {"aprovado_juiz": None, "erro": f"juiz: {erro}"}


def executar_bateria(
    casos,
    modelo,
    versao_prompt,
    prompt_sistema,
    modelo_juiz=None,
    usar_juiz=True,
    cliente=None,
    db_path=None,
    descricao="",
    arquivo_casos="",
    split="",
    permitidos=None,
    ao_progredir=None,
):
    """Roda todos os casos em um modelo, salva no banco e devolve o ID da execução.

    ao_progredir(fase, indice, total, resultado) é chamado a cada caso.
    """
    modelo_juiz = (modelo_juiz or modelo_juiz_configurado()) if usar_juiz else None
    initialize_database(db_path)
    execucao_id = create_run(
        descricao,
        db_path=db_path,
        origem="bateria",
        modelo=modelo,
        versao_prompt=versao_prompt,
        prompt_sistema=prompt_sistema,
        modelo_juiz=modelo_juiz,
        versao_prompt_juiz=VERSAO_PROMPT_JUIZ if usar_juiz else None,
        arquivo_casos=str(arquivo_casos),
        split=split,
    )
    logger.info(
        "execucao=%s inicio modelo=%s versao_prompt=%s juiz=%s casos=%s",
        execucao_id, modelo, versao_prompt, modelo_juiz, len(casos),
    )

    salvos = []
    for indice, caso in enumerate(casos, start=1):
        resultado = responder_caso(caso, modelo, prompt_sistema, cliente=cliente, permitidos=permitidos)
        resultado["id"] = save_result(execucao_id, resultado, db_path=db_path)
        salvos.append(resultado)

        if resultado.get("erro"):
            logger.warning("execucao=%s caso=%s erro=%s", execucao_id, caso["id"], resultado["erro"])
        else:
            logger.info(
                "execucao=%s fase=resposta caso=%s entrada=%r saida=%r tempo=%.2fs baseline=%s",
                execucao_id, caso["id"], caso["pergunta"][:80],
                (resultado.get("resposta") or "")[:120],
                resultado.get("tempo_resposta") or 0, resultado.get("aprovado_baseline"),
            )
        if ao_progredir:
            ao_progredir("resposta", indice, len(casos), resultado)

    if usar_juiz:
        # Tira o modelo avaliado da memória antes de carregar o juiz:
        # em máquinas com 8 GB os dois juntos não cabem.
        if modelo != modelo_juiz:
            liberar_modelo(modelo, cliente=cliente)
            logger.info("execucao=%s modelo %s descarregado antes do juiz", execucao_id, modelo)
        for indice, resultado in enumerate(salvos, start=1):
            if resultado.get("erro"):
                continue
            julgamento = julgar_resultado(resultado, modelo_juiz, cliente=cliente)
            atualizar_julgamento(resultado["id"], julgamento, db_path=db_path)
            resultado.update(julgamento)

            if julgamento.get("erro"):
                logger.warning("execucao=%s caso=%s erro=%s", execucao_id, resultado["caso_id"], julgamento["erro"])
            else:
                logger.info(
                    "execucao=%s fase=juiz caso=%s juiz=%s tempo=%.2fs motivo=%r",
                    execucao_id, resultado["caso_id"], julgamento["aprovado_juiz"],
                    julgamento.get("tempo_juiz") or 0, (julgamento.get("justificativa_juiz") or "")[:150],
                )
            if ao_progredir:
                ao_progredir("juiz", indice, len(salvos), resultado)

    logger.info("execucao=%s fim", execucao_id)
    return execucao_id

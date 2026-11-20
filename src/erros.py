"""Coleta os casos de falha do banco e gera uma imagem (estilo print) para cada um.

As imagens são montadas a partir dos dados reais gravados pelas baterias
(eval/avaliacoes.db): não há texto escrito à mão. Cada imagem traz no rodapé
a execução e o resultado de origem, para conferência.

Tipos de erro:
- falha_execucao: o modelo ou o juiz falhou (fora do ar, formato inválido) e o sistema tratou.
- modelo_errou: o humano reprovou a resposta; sem nota humana, juiz e baseline reprovaram.
- juiz_errou: o veredito do juiz diverge da nota humana.
- baseline_errou: o veredito do baseline diverge da nota humana.
- revisar: sem nota humana, juiz e baseline discordam. Não dá para saber quem
  errou sem uma pessoa avaliar (o humano é a única referência confiável).
"""

import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src import results_store

TIPOS = {
    "falha_execucao": ("Falha de execução tratada", (192, 57, 43)),
    "modelo_errou": ("Modelo respondeu errado", (211, 84, 0)),
    "juiz_errou": ("Juiz divergiu do humano", (142, 68, 173)),
    "baseline_errou": ("Baseline divergiu do humano", (41, 128, 185)),
    "revisar": ("Juiz e baseline divergem: avaliar à mão", (120, 120, 120)),
}

FONTES = {
    "normal": ["arial.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "negrito": ["arialbd.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": ["consola.ttf", "DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}

LARGURA = 1200
MARGEM = 36
COR_FUNDO = (255, 255, 255)
COR_BARRA = (38, 50, 56)
COR_TEXTO = (33, 33, 33)
COR_ROTULO = (96, 125, 139)
COR_CAIXA = (245, 247, 248)


def _fonte(tipo, tamanho):
    for nome in FONTES[tipo]:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(size=tamanho)


def classificar(r):
    """Lista os tipos de erro de um resultado (vazia se não houver erro)."""
    if r.get("erro"):
        return ["falha_execucao"]

    humano, juiz, baseline = r.get("aprovado_humano"), r.get("aprovado_juiz"), r.get("aprovado_baseline")

    if humano is None:
        if juiz is None or baseline is None:
            return []
        if juiz != baseline:
            return ["revisar"]
        return ["modelo_errou"] if juiz is False else []

    tipos = []
    if humano is False:
        tipos.append("modelo_errou")
    if juiz is not None and juiz != humano:
        tipos.append("juiz_errou")
    if baseline is not None and baseline != humano:
        tipos.append("baseline_errou")
    return tipos


def coletar_erros(resultados, tipos=None):
    """Resultados com erro, cada um acompanhado da lista de tipos."""
    erros = []
    for r in resultados:
        encontrados = classificar(r)
        if tipos:
            encontrados = [t for t in encontrados if t in tipos]
        if encontrados:
            erros.append({**r, "tipos_erro": encontrados})
    return erros


def _quebrar(texto, fonte, largura):
    """Quebra o texto em linhas que cabem na largura (em pixels)."""
    linhas = []
    for paragrafo in (texto or "").splitlines() or [""]:
        atual = ""
        for palavra in paragrafo.split(" "):
            tentativa = f"{atual} {palavra}".strip()
            if fonte.getlength(tentativa) <= largura:
                atual = tentativa
                continue
            if atual:
                linhas.append(atual)
            while fonte.getlength(palavra) > largura:  # palavra maior que a linha
                corte = len(palavra)
                while corte > 1 and fonte.getlength(palavra[:corte]) > largura:
                    corte -= 1
                linhas.append(palavra[:corte])
                palavra = palavra[corte:]
            atual = palavra
        linhas.append(atual)
    return linhas


def _veredito(valor):
    return {True: "APROVADO", False: "REPROVADO", None: "sem nota"}[valor]


def gerar_imagem(erro, execucao, caminho):
    """Desenha o 'print' de um caso de falha e salva em PNG."""
    f_titulo = _fonte("negrito", 20)
    f_rotulo = _fonte("negrito", 15)
    f_texto = _fonte("normal", 17)
    f_mono = _fonte("mono", 16)
    f_rodape = _fonte("normal", 13)
    largura_util = LARGURA - 2 * MARGEM - 24

    blocos = [
        ("Pergunta", erro.get("pergunta"), f_texto),
        ("Resposta de referência", erro.get("resposta_referencia") or "-", f_texto),
        ("Resposta do modelo", erro.get("resposta") or "(vazia)", f_mono),
    ]
    if erro.get("justificativa_juiz"):
        blocos.append(("Justificativa do juiz", erro["justificativa_juiz"], f_texto))
    if erro.get("erro"):
        blocos.append(("Erro registrado pelo sistema", erro["erro"], f_mono))

    # Calcula a altura antes de desenhar.
    altura_blocos = 0
    linhas_por_bloco = []
    for _, texto, fonte in blocos:
        linhas = _quebrar(str(texto), fonte, largura_util)
        linhas_por_bloco.append(linhas)
        altura_blocos += 28 + len(linhas) * 24 + 26
    altura = 56 + 150 + altura_blocos + 70

    img = Image.new("RGB", (LARGURA, altura), COR_FUNDO)
    d = ImageDraw.Draw(img)

    # Barra de título, como uma janela.
    d.rectangle([0, 0, LARGURA, 48], fill=COR_BARRA)
    for i, cor in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([18 + i * 26, 16, 34 + i * 26, 32], fill=cor)
    d.text((110, 13), "Plataforma de avaliação de LLMs — caso de falha", font=f_titulo, fill=(236, 239, 241))

    y = 72
    x = MARGEM
    for tipo in erro["tipos_erro"]:
        nome, cor = TIPOS[tipo]
        w = f_rotulo.getlength(nome) + 24
        d.rounded_rectangle([x, y, x + w, y + 30], radius=15, fill=cor)
        d.text((x + 12, y + 6), nome, font=f_rotulo, fill=(255, 255, 255))
        x += w + 10

    y += 46
    cabecalho = (
        f"Caso {erro.get('caso_id') or '-'}  ·  categoria {erro.get('categoria') or '-'}  ·  "
        f"modelo {erro.get('modelo')}  ·  prompt {execucao.get('versao_prompt') or '-'}  ·  "
        f"juiz {execucao.get('modelo_juiz') or '-'}"
    )
    d.text((MARGEM, y), cabecalho, font=f_texto, fill=COR_TEXTO)
    y += 32
    vereditos = (
        f"Baseline: {_veredito(erro.get('aprovado_baseline'))}     "
        f"Juiz: {_veredito(erro.get('aprovado_juiz'))}     "
        f"Humano: {_veredito(erro.get('aprovado_humano'))}"
        + (f" ({erro['avaliador_humano']})" if erro.get("avaliador_humano") else "")
    )
    d.text((MARGEM, y), vereditos, font=f_rotulo, fill=COR_TEXTO)
    y += 40

    for (rotulo, _, fonte), linhas in zip(blocos, linhas_por_bloco, strict=False):
        d.text((MARGEM, y), rotulo.upper(), font=f_rotulo, fill=COR_ROTULO)
        y += 26
        altura_caixa = len(linhas) * 24 + 16
        d.rounded_rectangle([MARGEM, y, LARGURA - MARGEM, y + altura_caixa], radius=8, fill=COR_CAIXA)
        for i, linha in enumerate(linhas):
            d.text((MARGEM + 12, y + 8 + i * 24), linha, font=fonte, fill=COR_TEXTO)
        y += altura_caixa + 26

    rodape = (
        f"Gerado de {Path(results_store.DATABASE_PATH).name}  ·  "
        f"execução #{execucao.get('id')} ({execucao.get('data_hora')})  ·  "
        f"resultado #{erro.get('id')}  ·  tempo {erro.get('tempo_resposta') or 0:.2f}s  ·  "
        f"imagem gerada em {datetime.now():%Y-%m-%d %H:%M:%S}"
    )
    d.line([MARGEM, altura - 50, LARGURA - MARGEM, altura - 50], fill=(224, 224, 224), width=1)
    d.text((MARGEM, altura - 38), rodape, font=f_rodape, fill=COR_ROTULO)

    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    img.save(caminho)
    return caminho


def _resumo_md(texto, limite=70):
    texto = " ".join((texto or "").split()).replace("|", "\\|")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


PENDENTE = "_a preencher_"


def _causas_existentes(indice):
    """Lê as causas já escritas pelo grupo no README.md, para não perdê-las ao regenerar."""
    if not indice.exists():
        return {}
    causas = {}
    for linha in indice.read_text(encoding="utf-8").splitlines():
        if not linha.startswith("| [erro_"):
            continue
        colunas = [c.strip() for c in linha.strip().strip("|").split(" | ")]
        arquivo = colunas[0].split("]")[0].lstrip("[")
        if colunas[-1] and colunas[-1] != PENDENTE:
            causas[arquivo] = colunas[-1]
    return causas


def exportar_erros(execucoes_resultados, pasta, tipos=None):
    """Gera os PNGs, erros.json e README.md (índice) na pasta. Devolve a lista de erros."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    causas = _causas_existentes(pasta / "README.md")
    for antigo in pasta.glob("erro_*.png"):
        antigo.unlink()

    todos = []
    for execucao, resultados in execucoes_resultados:
        for erro in coletar_erros(resultados, tipos):
            nome = f"erro_exec{execucao['id']}_{erro.get('caso_id') or erro['id']}_{erro['tipos_erro'][0]}.png"
            gerar_imagem(erro, execucao, pasta / nome)
            todos.append({**erro, "arquivo": nome, "execucao": execucao["id"],
                          "versao_prompt": execucao.get("versao_prompt")})

    (pasta / "erros.json").write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

    contagem = {t: sum(1 for e in todos if t in e["tipos_erro"]) for t in TIPOS}
    linhas = [
        "# Casos de falha",
        "",
        "Imagens geradas automaticamente a partir dos resultados gravados no banco",
        "(`python -m src.cli erros <execuções>`). Cada imagem informa no rodapé a",
        "execução e o resultado de origem. A coluna **Causa provável** é preenchida",
        "pelo grupo após analisar cada caso (exigência da evidência 6).",
        "",
        "| Tipo | Quantidade |",
        "|---|---|",
        *[f"| {TIPOS[t][0]} | {n} |" for t, n in contagem.items()],
        "",
        "| Imagem | Execução | Caso | Modelo | Prompt | Tipos | Resposta do modelo | Causa provável |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in todos:
        tipos_txt = ", ".join(TIPOS[t][0] for t in e["tipos_erro"])
        linhas.append(
            f"| [{e['arquivo']}]({e['arquivo']}) | {e['execucao']} | {e.get('caso_id') or '-'} | "
            f"{e['modelo']} | {e['versao_prompt'] or '-'} | {tipos_txt} | "
            f"{_resumo_md(e.get('resposta') or e.get('erro'))} | {causas.get(e['arquivo'], PENDENTE)} |"
        )
    (pasta / "README.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return todos

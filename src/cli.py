"""Linha de comando da plataforma de avaliação.

Exemplos:
    python -m src.cli rodar --versao v1
    python -m src.cli rodar --versao v2_piorado --modelos gemma3:4b
    python -m src.cli execucoes
    python -m src.cli comparar 1 2 --limiar 5
    python -m src.cli concordancia 1 2 3
    python -m src.cli exportar 1 2 --saida eval/resultados
    python -m src.cli importar-humano eval/resultados/rotulos.csv --avaliador Ana
    python -m src.cli erros 1 2          # prints dos casos de falha em evidencias/erros/
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.casos import CASOS_PADRAO, RAIZ, carregar_casos, carregar_prompt
from src.evaluation import (
    CAMPOS_AVALIADOR,
    calculate_metrics,
    concordancia,
    detectar_regressao,
    interpretar_kappa,
)
from src.judge import modelo_juiz_configurado
from src.model_runner import criar_cliente, modelos_configurados, modelos_instalados
from src.results_store import (
    initialize_database,
    listar_execucoes,
    listar_resultados,
    obter_execucao,
    registrar_avaliacao_humana,
)
from src.runner import executar_bateria

LOGS_DIR = RAIZ / "eval" / "logs"


def configurar_logs(nome_arquivo=None):
    """Logs com data e hora no terminal e, opcionalmente, em eval/logs/."""
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    raiz = logging.getLogger("avaliacao")
    raiz.setLevel(logging.INFO)
    raiz.handlers.clear()

    terminal = logging.StreamHandler()
    terminal.setFormatter(formato)
    raiz.addHandler(terminal)

    if nome_arquivo:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        arquivo = logging.FileHandler(LOGS_DIR / nome_arquivo, encoding="utf-8")
        arquivo.setFormatter(formato)
        raiz.addHandler(arquivo)
        return LOGS_DIR / nome_arquivo
    return None


def _fmt(valor, sufixo=""):
    return "-" if valor is None else f"{valor}{sufixo}"


def cmd_rodar(args):
    casos = carregar_casos(args.casos, split=args.split, limite=args.limite)
    prompt = carregar_prompt(args.versao)
    modelos = [m.strip() for m in args.modelos.split(",")] if args.modelos else modelos_configurados()
    juiz = None if args.sem_juiz else (args.juiz or modelo_juiz_configurado())

    cliente = criar_cliente()
    instalados = modelos_instalados(cliente)
    necessarios = modelos + ([juiz] if juiz else [])
    faltando = [m for m in necessarios if m not in instalados]
    if faltando:
        print(f"Modelos não instalados no Ollama: {', '.join(faltando)}", file=sys.stderr)
        print("Instale com: ollama pull <modelo>", file=sys.stderr)
        return 2

    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = configurar_logs(f"bateria-{carimbo}-{args.versao}.log")

    ids = []
    for modelo in modelos:
        def progresso(fase, i, total, resultado, modelo=modelo):
            if i % 10 == 0 or i == total:
                print(f"  {modelo} [{fase}]: {i}/{total}", file=sys.stderr)

        execucao_id = executar_bateria(
            casos, modelo, args.versao, prompt,
            modelo_juiz=juiz, usar_juiz=not args.sem_juiz, cliente=cliente,
            descricao=args.descricao, arquivo_casos=Path(args.casos).name,
            split=args.split, permitidos=modelos, ao_progredir=progresso,
        )
        ids.append(execucao_id)
        metricas = calculate_metrics(listar_resultados(execucao_id))
        print(
            f"Execução {execucao_id} | {modelo} | versão {args.versao} | "
            f"juiz {_fmt(metricas['taxa_acerto_juiz'], '%')} | "
            f"baseline {_fmt(metricas['taxa_acerto_baseline'], '%')} | "
            f"tempo total {metricas['tempo_total']}s | tokens {metricas['tokens_total']}"
        )

    print(f"Execuções criadas: {' '.join(map(str, ids))}")
    print(f"Log: {log}")
    return 0


def cmd_execucoes(args):
    execucoes = listar_execucoes(origem=None if args.todas else "bateria")
    if not execucoes:
        print("Nenhuma execução registrada.")
        return 0
    print(f"{'ID':>4}  {'Data/hora':19}  {'Modelo':14}  {'Versão':12}  {'N':>4}  "
          f"{'Juiz':>7}  {'Base':>7}  {'Humano':>7}  Descrição")
    for e in execucoes:
        m = calculate_metrics(listar_resultados(e["id"]))
        print(
            f"{e['id']:>4}  {e['data_hora'] or '':19}  {(e['modelo'] or '-'):14}  "
            f"{(e['versao_prompt'] or '-'):12}  {m['total']:>4}  "
            f"{_fmt(m['taxa_acerto_juiz'], '%'):>7}  {_fmt(m['taxa_acerto_baseline'], '%'):>7}  "
            f"{_fmt(m['taxa_acerto_humano'], '%'):>7}  {e['descricao'] or ''}"
        )
    return 0


def cmd_comparar(args):
    base, nova = obter_execucao(args.base), obter_execucao(args.nova)
    if not base or not nova:
        print("Execução não encontrada.", file=sys.stderr)
        return 2

    campo = CAMPOS_AVALIADOR[args.campo]
    r = detectar_regressao(
        listar_resultados(args.base), listar_resultados(args.nova), campo=campo, limiar=args.limiar,
    )
    print(f"Base : execução {args.base} ({base['modelo']}, versão {base['versao_prompt']}) -> {r['taxa_base']}%")
    print(f"Nova : execução {args.nova} ({nova['modelo']}, versão {nova['versao_prompt']}) -> {r['taxa_nova']}%")
    print(f"Delta: {r['delta']:+} pontos (limiar {r['limiar']})")
    if r["casos_que_pioraram"]:
        print(f"Casos que passaram a falhar ({len(r['casos_que_pioraram'])}): "
              f"{', '.join(r['casos_que_pioraram'])}")

    if r["regressao"]:
        print("REGRESSÃO DETECTADA")
        return 1
    print("Sem regressão.")
    return 0


def cmd_concordancia(args):
    resultados = [r for eid in args.execucoes for r in listar_resultados(eid)]
    for nome in ("juiz", "baseline"):
        c = concordancia(resultados, CAMPOS_AVALIADOR[nome], "aprovado_humano")
        print(f"\n{nome.upper()} x HUMANO  (n = {c['n']})")
        if not c["n"]:
            print("  Sem casos avaliados pelos dois. Faça a avaliação humana no painel.")
            continue
        print(f"  Acordo: {c['acordo_percentual']}%")
        print(f"  Kappa de Cohen: {c['kappa']} ({interpretar_kappa(c['kappa'])})")
        print(f"  Matriz: {c['matriz']}")
        if args.detalhes and c["divergencias"]:
            print("  Divergências:")
            for d in c["divergencias"]:
                print(f"   - [{d['caso_id']}] {d['modelo']} | {nome}={d[CAMPOS_AVALIADOR[nome]]} "
                      f"humano={d['aprovado_humano']} | resposta: {(d['resposta'] or '')[:100]!r}")
                if nome == "juiz":
                    print(f"     justificativa do juiz: {d.get('justificativa_juiz')!r}")
    return 0


def cmd_exportar(args):
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    resumo = []
    for eid in args.execucoes:
        execucao = obter_execucao(eid)
        if not execucao:
            print(f"Execução {eid} não encontrada.", file=sys.stderr)
            return 2
        resultados = listar_resultados(eid)
        if resultados:
            caminho_csv = saida / f"execucao_{eid}.csv"
            with open(caminho_csv, "w", newline="", encoding="utf-8") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=list(resultados[0]))
                escritor.writeheader()
                escritor.writerows(resultados)
            print(f"Gravado {caminho_csv}")
        resumo.append({
            "execucao": {k: execucao[k] for k in ("id", "data_hora", "modelo", "versao_prompt", "modelo_juiz", "split")},
            "metricas": calculate_metrics(resultados),
        })

    juntos = [r for eid in args.execucoes for r in listar_resultados(eid)]
    conc = {}
    for nome in ("juiz", "baseline"):
        c = concordancia(juntos, CAMPOS_AVALIADOR[nome])
        c.pop("divergencias")
        conc[f"{nome}_x_humano"] = c

    caminho_json = saida / "metricas.json"
    caminho_json.write_text(
        json.dumps({"execucoes": resumo, "concordancia": conc}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Gravado {caminho_json}")
    return 0


def cmd_erros(args):
    from src.erros import TIPOS, exportar_erros

    ids = args.execucoes or [e["id"] for e in listar_execucoes(origem="bateria")]
    pares = []
    for eid in ids:
        execucao = obter_execucao(eid)
        if not execucao:
            print(f"Execução {eid} não encontrada.", file=sys.stderr)
            return 2
        pares.append((execucao, listar_resultados(eid)))

    erros = exportar_erros(pares, args.saida, tipos=args.tipo)
    print(f"{len(erros)} casos de falha exportados para {args.saida}")
    for tipo, (nome, _) in TIPOS.items():
        print(f"  {nome}: {sum(1 for e in erros if tipo in e['tipos_erro'])}")
    return 0


def _ler_booleano(valor):
    texto = (valor or "").strip().lower()
    if texto in ("1", "true", "sim", "s", "aprovado", "aprovada"):
        return True
    if texto in ("0", "false", "nao", "não", "n", "reprovado", "reprovada"):
        return False
    return None


def cmd_importar_humano(args):
    total = 0
    with open(args.arquivo, encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            nota = _ler_booleano(linha.get("aprovado_humano"))
            if nota is None:
                continue
            registrar_avaliacao_humana(int(linha["id"]), nota, args.avaliador)
            total += 1
    print(f"{total} avaliações humanas importadas.")
    return 0


def criar_parser():
    parser = argparse.ArgumentParser(prog="python -m src.cli", description="Plataforma de avaliação de LLMs")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("rodar", help="Roda a bateria de casos nos modelos")
    p.add_argument("--versao", default="v1", help="Versão do prompt (arquivo eval/prompts/<versao>.txt)")
    p.add_argument("--modelos", help="Lista separada por vírgula (padrão: MODELOS_AVALIADOS)")
    p.add_argument("--casos", default=str(CASOS_PADRAO))
    p.add_argument("--split", default="teste", choices=["teste", "calibracao", "todos"])
    p.add_argument("--limite", type=int, help="Roda só os N primeiros casos")
    p.add_argument("--juiz", help="Modelo juiz (padrão: MODELO_JUIZ ou qwen2.5:7b)")
    p.add_argument("--sem-juiz", action="store_true", help="Só baseline, sem LLM juiz")
    p.add_argument("--descricao", default="")
    p.set_defaults(func=cmd_rodar)

    p = sub.add_parser("execucoes", help="Lista as execuções e suas métricas")
    p.add_argument("--todas", action="store_true", help="Inclui perguntas manuais do painel")
    p.set_defaults(func=cmd_execucoes)

    p = sub.add_parser("comparar", help="Detecta regressão entre duas execuções (sai com código 1)")
    p.add_argument("base", type=int)
    p.add_argument("nova", type=int)
    p.add_argument("--limiar", type=float, default=5.0, help="Queda máxima aceita, em pontos percentuais")
    p.add_argument("--campo", default="juiz", choices=list(CAMPOS_AVALIADOR))
    p.set_defaults(func=cmd_comparar)

    p = sub.add_parser("concordancia", help="Concordância juiz x humano e baseline x humano")
    p.add_argument("execucoes", type=int, nargs="+")
    p.add_argument("--detalhes", action="store_true", help="Lista os casos de divergência")
    p.set_defaults(func=cmd_concordancia)

    p = sub.add_parser("exportar", help="Exporta CSV e metricas.json para evidências")
    p.add_argument("execucoes", type=int, nargs="+")
    p.add_argument("--saida", default=str(RAIZ / "eval" / "resultados"))
    p.set_defaults(func=cmd_exportar)

    p = sub.add_parser("erros", help="Gera imagens (prints) dos casos de falha em evidencias/erros")
    p.add_argument("execucoes", type=int, nargs="*", help="IDs das execuções (padrão: todas as baterias)")
    p.add_argument("--saida", default=str(RAIZ / "evidencias" / "erros"))
    p.add_argument("--tipo", action="append",
                   choices=["falha_execucao", "modelo_errou", "juiz_errou", "baseline_errou", "revisar"],
                   help="Filtra por tipo (pode repetir)")
    p.set_defaults(func=cmd_erros)

    p = sub.add_parser("importar-humano", help="Importa notas humanas de um CSV exportado")
    p.add_argument("arquivo")
    p.add_argument("--avaliador", required=True)
    p.set_defaults(func=cmd_importar_humano)

    return parser


def main(argv=None):
    # Acentos corretos no terminal do Windows.
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    args = criar_parser().parse_args(argv)
    initialize_database()
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

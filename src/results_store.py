"""Armazenamento das execuções e resultados em SQLite."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH")
    or Path(__file__).resolve().parent.parent / "eval" / "avaliacoes.db"
)

COLUNAS_EXECUCOES = {
    "data_hora": "TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))",
    "descricao": "TEXT",
    "origem": "TEXT NOT NULL DEFAULT 'manual'",
    "modelo": "TEXT",
    "versao_prompt": "TEXT",
    "prompt_sistema": "TEXT",
    "modelo_juiz": "TEXT",
    "versao_prompt_juiz": "TEXT",
    "arquivo_casos": "TEXT",
    "split": "TEXT",
}

COLUNAS_RESULTADOS = {
    "execucao_id": "INTEGER NOT NULL REFERENCES execucoes(id) ON DELETE CASCADE",
    "caso_id": "TEXT",
    "categoria": "TEXT",
    "modelo": "TEXT NOT NULL",
    "pergunta": "TEXT NOT NULL",
    "resposta_referencia": "TEXT",
    "resposta": "TEXT",
    "aprovado_baseline": "INTEGER",
    "aprovado_juiz": "INTEGER",
    "justificativa_juiz": "TEXT",
    "aprovado_humano": "INTEGER",
    "avaliador_humano": "TEXT",
    "tempo_resposta": "REAL",
    "tokens_entrada": "INTEGER DEFAULT 0",
    "tokens_saida": "INTEGER DEFAULT 0",
    "tempo_juiz": "REAL",
    "tokens_juiz": "INTEGER DEFAULT 0",
    "erro": "TEXT",
}

CAMPOS_BOOLEANOS = ("aprovado_baseline", "aprovado_juiz", "aprovado_humano")


@contextmanager
def conectar(db_path=None):
    """Abre a conexão, faz commit ao final (ou rollback em erro) e sempre fecha."""
    caminho = Path(db_path or DATABASE_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _criar_ou_migrar(conexao, tabela, colunas):
    definicoes = ",\n".join(f"{nome} {tipo}" for nome, tipo in colunas.items())
    conexao.execute(
        f"CREATE TABLE IF NOT EXISTS {tabela} (\n"
        f"id INTEGER PRIMARY KEY AUTOINCREMENT,\n{definicoes})"
    )
    # Bancos criados por versões antigas ganham as colunas novas.
    existentes = {linha["name"] for linha in conexao.execute(f"PRAGMA table_info({tabela})")}
    for nome, tipo in colunas.items():
        if nome not in existentes:
            tipo_simples = tipo.split(" REFERENCES")[0].replace("NOT NULL", "")
            if "DEFAULT (" in tipo_simples:
                tipo_simples = "TEXT"
            conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo_simples}")


def initialize_database(db_path=None):
    """Cria (ou atualiza) as tabelas do banco."""
    with conectar(db_path) as conexao:
        _criar_ou_migrar(conexao, "execucoes", COLUNAS_EXECUCOES)
        _criar_ou_migrar(conexao, "resultados", COLUNAS_RESULTADOS)
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_resultados_execucao ON resultados(execucao_id)"
        )


def _para_int(valor):
    return None if valor is None else int(bool(valor))


def _linha_para_dict(linha):
    dados = dict(linha)
    for campo in CAMPOS_BOOLEANOS:
        if campo in dados and dados[campo] is not None:
            dados[campo] = bool(dados[campo])
    return dados


def create_run(descricao="", db_path=None, **campos):
    """Registra uma nova execução e retorna seu ID.

    Campos opcionais: origem, modelo, versao_prompt, prompt_sistema,
    modelo_juiz, versao_prompt_juiz, arquivo_casos, split.
    """
    desconhecidos = set(campos) - set(COLUNAS_EXECUCOES)
    if desconhecidos:
        raise ValueError(f"Campos desconhecidos: {', '.join(sorted(desconhecidos))}")

    valores = {"descricao": descricao, **campos}
    nomes = ", ".join(valores)
    marcadores = ", ".join("?" for _ in valores)
    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            f"INSERT INTO execucoes ({nomes}) VALUES ({marcadores})",
            tuple(valores.values()),
        )
        return cursor.lastrowid


def save_result(execucao_id, resultado, db_path=None):
    """Salva o resultado de uma resposta e retorna o ID do resultado."""
    valores = {
        "execucao_id": execucao_id,
        "caso_id": resultado.get("caso_id"),
        "categoria": resultado.get("categoria"),
        "modelo": resultado["modelo"],
        "pergunta": resultado["pergunta"],
        "resposta_referencia": resultado.get("resposta_referencia"),
        "resposta": resultado.get("resposta", ""),
        "aprovado_baseline": _para_int(resultado.get("aprovado_baseline")),
        "aprovado_juiz": _para_int(resultado.get("aprovado_juiz")),
        "justificativa_juiz": resultado.get("justificativa_juiz"),
        "aprovado_humano": _para_int(resultado.get("aprovado_humano")),
        "avaliador_humano": resultado.get("avaliador_humano"),
        "tempo_resposta": resultado.get("tempo_resposta"),
        "tokens_entrada": resultado.get("tokens_entrada", 0),
        "tokens_saida": resultado.get("tokens_saida", 0),
        "tempo_juiz": resultado.get("tempo_juiz"),
        "tokens_juiz": resultado.get("tokens_juiz", 0),
        "erro": resultado.get("erro"),
    }
    nomes = ", ".join(valores)
    marcadores = ", ".join("?" for _ in valores)
    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            f"INSERT INTO resultados ({nomes}) VALUES ({marcadores})",
            tuple(valores.values()),
        )
        return cursor.lastrowid


def registrar_avaliacao_humana(resultado_id, aprovado, avaliador="", db_path=None):
    """Grava (ou limpa, com aprovado=None) a nota humana de um resultado."""
    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            "UPDATE resultados SET aprovado_humano = ?, avaliador_humano = ? WHERE id = ?",
            (_para_int(aprovado), avaliador or None, resultado_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Resultado {resultado_id} não encontrado")


CAMPOS_JULGAMENTO = ("aprovado_juiz", "justificativa_juiz", "tempo_juiz", "tokens_juiz", "erro")


def atualizar_julgamento(resultado_id, dados, db_path=None):
    """Grava o veredito do juiz (e eventual erro) em um resultado já salvo."""
    campos = {k: dados[k] for k in CAMPOS_JULGAMENTO if k in dados}
    if "aprovado_juiz" in campos:
        campos["aprovado_juiz"] = _para_int(campos["aprovado_juiz"])
    if not campos:
        return
    atribuicoes = ", ".join(f"{nome} = ?" for nome in campos)
    with conectar(db_path) as conexao:
        conexao.execute(
            f"UPDATE resultados SET {atribuicoes} WHERE id = ?",
            (*campos.values(), resultado_id),
        )


def obter_execucao(execucao_id, db_path=None):
    with conectar(db_path) as conexao:
        linha = conexao.execute(
            "SELECT * FROM execucoes WHERE id = ?", (execucao_id,)
        ).fetchone()
        return dict(linha) if linha else None


def listar_execucoes(origem=None, db_path=None):
    """Execuções em ordem decrescente, com a quantidade de resultados de cada uma."""
    consulta = """
        SELECT e.*, COUNT(r.id) AS total_resultados
        FROM execucoes e
        LEFT JOIN resultados r ON r.execucao_id = e.id
        {filtro}
        GROUP BY e.id
        ORDER BY e.id DESC
    """
    with conectar(db_path) as conexao:
        if origem:
            linhas = conexao.execute(
                consulta.format(filtro="WHERE e.origem = ?"), (origem,)
            ).fetchall()
        else:
            linhas = conexao.execute(consulta.format(filtro="")).fetchall()
        return [dict(linha) for linha in linhas]


def listar_resultados(execucao_id=None, db_path=None):
    """Resultados de uma execução (ou de todas), com campos booleanos convertidos."""
    with conectar(db_path) as conexao:
        if execucao_id is None:
            linhas = conexao.execute("SELECT * FROM resultados ORDER BY id").fetchall()
        else:
            linhas = conexao.execute(
                "SELECT * FROM resultados WHERE execucao_id = ? ORDER BY id",
                (execucao_id,),
            ).fetchall()
        return [_linha_para_dict(linha) for linha in linhas]

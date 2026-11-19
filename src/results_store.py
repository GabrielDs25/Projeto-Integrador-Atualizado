
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "eval" / "avaliacoes.db"


def conectar(db_path=DATABASE_PATH):
    """Abre uma conexão com o banco SQLite."""
    caminho = Path(db_path)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def initialize_database(db_path=DATABASE_PATH):
    """Cria as tabelas necessárias para armazenar as avaliações."""
    with conectar(db_path) as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS execucoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                descricao TEXT
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execucao_id INTEGER NOT NULL,
                modelo TEXT NOT NULL,
                pergunta TEXT NOT NULL,
                resposta TEXT,
                aprovado INTEGER,
                tempo_resposta REAL,
                tokens_entrada INTEGER DEFAULT 0,
                tokens_saida INTEGER DEFAULT 0,
                FOREIGN KEY (execucao_id) REFERENCES execucoes(id)
            )
        """)

        conexao.execute("PRAGMA foreign_keys = ON")


def create_run(descricao="", db_path=DATABASE_PATH):
    """Registra uma nova execução e retorna seu ID."""
    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            "INSERT INTO execucoes (descricao) VALUES (?)",
            (descricao,)
        )
        return cursor.lastrowid


def save_result(execucao_id, resultado, db_path=DATABASE_PATH):
    """Salva o resultado de uma resposta de modelo."""
    with conectar(db_path) as conexao:
        conexao.execute("""
            INSERT INTO resultados (
                execucao_id,
                modelo,
                pergunta,
                resposta,
                aprovado,
                tempo_resposta,
                tokens_entrada,
                tokens_saida
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execucao_id,
            resultado["modelo"],
            resultado["pergunta"],
            resultado.get("resposta", ""),
            None if resultado.get("aprovado") is None
            else int(resultado["aprovado"]),
            resultado.get("tempo_resposta"),
            resultado.get("tokens_entrada", 0),
            resultado.get("tokens_saida", 0),
        ))


def listar_resultados(execucao_id=None, db_path=DATABASE_PATH):
    """Consulta os resultados armazenados."""
    with conectar(db_path) as conexao:
        if execucao_id is None:
            consulta = """
                SELECT * FROM resultados ORDER BY id DESC
            """
            linhas = conexao.execute(consulta).fetchall()
        else:
            consulta = """
                SELECT * FROM resultados
                WHERE execucao_id = ?
                ORDER BY id DESC
            """
            linhas = conexao.execute(
                consulta, (execucao_id,)
            ).fetchall()

        return [dict(linha) for linha in linhas]

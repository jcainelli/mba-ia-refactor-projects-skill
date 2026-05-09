import sqlite3
import bcrypt
from flask import g

from src.config.settings import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente',
    total REAL NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
);
"""


def _connect():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create schema if missing and seed if empty. Idempotent."""
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        if conn.execute("SELECT COUNT(*) AS c FROM produtos").fetchone()["c"] == 0:
            _seed(conn)
            conn.commit()
    finally:
        conn.close()


def _seed(conn):
    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
        ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
    ]
    conn.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        produtos,
    )

    def _hash(pw):
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    usuarios = [
        ("Admin", "admin@loja.com", _hash(settings.SEED_ADMIN_PASSWORD), "admin"),
        ("João Silva", "joao@email.com", _hash(settings.SEED_USER_PASSWORD), "cliente"),
        ("Maria Santos", "maria@email.com", _hash(settings.SEED_USER_PASSWORD), "cliente"),
    ]
    conn.executemany(
        "INSERT INTO usuarios (nome, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )


def init_app(app):
    app.teardown_appcontext(close_db)

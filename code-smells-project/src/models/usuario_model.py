import bcrypt
from src.config.database import get_db


_PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")


def _to_public(row):
    if row is None:
        return None
    return {f: row[f] for f in _PUBLIC_FIELDS}


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, password_hash):
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def get_todos():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_public(r) for r in rows]


def get_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_public(row)


def get_por_email_full(email):
    """Returns the raw row (incl. password_hash). Use only in auth flow."""
    return get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def criar(nome, email, password, tipo="cliente"):
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hash_password(password), tipo),
    )
    db.commit()
    return cur.lastrowid

from src.config.database import get_db


_PUBLIC_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    if row is None:
        return None
    return {f: row[f] for f in _PUBLIC_FIELDS}


def get_todos():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [_to_dict(r) for r in rows]


def get_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row)


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    filters = ["1=1"]
    params = []
    if termo:
        filters.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        filters.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        filters.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        filters.append("preco <= ?")
        params.append(preco_max)
    rows = get_db().execute(
        "SELECT * FROM produtos WHERE " + " AND ".join(filters), params
    ).fetchall()
    return [_to_dict(r) for r in rows]

from src.config.database import get_db


def get_todos_com_itens():
    return _query_pedidos(usuario_id=None)


def get_por_usuario(usuario_id):
    return _query_pedidos(usuario_id=usuario_id)


def _query_pedidos(usuario_id=None):
    sql = """
        SELECT
            p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
            i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
    params = ()
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params = (usuario_id,)
    sql += " ORDER BY p.criado_em DESC, p.id, i.id"

    rows = get_db().execute(sql, params).fetchall()
    pedidos = {}
    order = []
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            order.append(pid)
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return [pedidos[pid] for pid in order]


def criar_com_itens(usuario_id, itens):
    """Atomically: validate stock, insert pedido + itens, decrement stock.

    Each item: {"produto_id": int, "quantidade": int}.
    Raises ValueError on stock/product issues.
    """
    db = get_db()
    try:
        produtos = {}
        total = 0.0
        for item in itens:
            produto_id = item["produto_id"]
            quantidade = item["quantidade"]
            row = db.execute(
                "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                (produto_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Produto {produto_id} não encontrado")
            if row["estoque"] < quantidade:
                raise ValueError(f"Estoque insuficiente para {row['nome']}")
            produtos[produto_id] = row
            total += row["preco"] * quantidade

        cur = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cur.lastrowid

        for item in itens:
            produto = produtos[item["produto_id"]]
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, produto["id"], item["quantidade"], produto["preco"]),
            )
            updated = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], produto["id"], item["quantidade"]),
            )
            if updated.rowcount == 0:
                raise ValueError(f"Estoque insuficiente para {produto['nome']}")

        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except Exception:
        db.rollback()
        raise


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def stats():
    row = get_db().execute("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(total), 0) AS faturamento,
            COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
            COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
            COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
    """).fetchone()
    return {
        "total_pedidos": row["total"],
        "faturamento": float(row["faturamento"] or 0),
        "pedidos_pendentes": row["pendentes"],
        "pedidos_aprovados": row["aprovados"],
        "pedidos_cancelados": row["cancelados"],
    }

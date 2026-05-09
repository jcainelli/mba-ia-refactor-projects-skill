from src.config.constants import DESCONTO_TIERS
from src.models import pedido_model


def calcular_desconto(faturamento):
    for limite, percentual in DESCONTO_TIERS:
        if faturamento > limite:
            return faturamento * percentual
    return 0.0


def gerar_relatorio_vendas():
    stats = pedido_model.stats()
    faturamento = float(stats["faturamento"])
    desconto = calcular_desconto(faturamento)
    total_pedidos = stats["total_pedidos"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": stats["pedidos_pendentes"],
        "pedidos_aprovados": stats["pedidos_aprovados"],
        "pedidos_cancelados": stats["pedidos_cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }

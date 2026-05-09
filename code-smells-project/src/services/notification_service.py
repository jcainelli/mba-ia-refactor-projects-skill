import logging

log = logging.getLogger(__name__)


def notify_pedido_criado(*, usuario_id, pedido_id):
    log.info("notification.pedido_criado pedido_id=%s usuario_id=%s", pedido_id, usuario_id)


def notify_pedido_status(*, pedido_id, status):
    log.info("notification.pedido_status pedido_id=%s status=%s", pedido_id, status)

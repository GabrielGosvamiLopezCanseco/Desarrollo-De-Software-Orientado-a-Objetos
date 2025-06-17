from enum import Enum
from datetime import datetime

class EstadoFactura(Enum):
    PENDIENTE = 'PENDIENTE'
    PAGADA = 'PAGADA'
    CONCILIADA = 'CONCILIADA'

class Factura:
    def __init__(self, id_factura: str, pedido_id: str, total: float):
        self.id = id_factura
        self.pedido_id = pedido_id
        self.total = total
        self.fecha_emision = datetime.now().date()
        self.estado = EstadoFactura.PENDIENTE
        self.fecha_pago = None

    def marcar_como_pagada(self):
        self.estado = EstadoFactura.PAGADA
        self.fecha_pago = datetime.now().date()

class Transaccion:
    def __init__(self, id_transaccion: str, monto: float, metodo_pago: str, factura_id: str):
        self.id = id_transaccion
        self.monto = monto
        self.metodo_pago = metodo_pago
        self.factura_id = factura_id
        self.fecha = datetime.now()
        self.estado = 'PENDIENTE'

    def conciliar(self):
        self.estado = 'CONCILIADA'
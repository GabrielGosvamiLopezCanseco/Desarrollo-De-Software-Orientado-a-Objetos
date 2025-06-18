# modelo.py
from enum import Enum
from datetime import datetime
from typing import Optional

class EstadoFactura(Enum):
    PENDIENTE = 'PENDIENTE'
    PAGADA_PARCIAL = 'PAGADA_PARCIAL'
    PAGADA = 'PAGADA'
    CONCILIADA = 'CONCILIADA'

class Factura:
    def __init__(self, id_factura: str, pedido_id: str, total: float, cliente: str):
        self.id = id_factura
        self.pedido_id = pedido_id
        self.total = total
        self.saldo_pendiente = total
        self.cliente = cliente  # Campo requerido
        self.fecha_emision = datetime.now().date()
        self.estado = EstadoFactura.PENDIENTE
        self.fecha_pago = None
        self.comprobante_pago = None

    def registrar_pago(self, monto: float, comprobante: Optional[str] = None):
        if monto <= 0:
            raise ValueError("El monto debe ser positivo")
            
        if monto > self.saldo_pendiente:
            raise ValueError("El pago excede el saldo pendiente")
        
        self.saldo_pendiente -= monto
        self.comprobante_pago = comprobante
        
        if self.saldo_pendiente == 0:
            self.estado = EstadoFactura.PAGADA
        else:
            self.estado = EstadoFactura.PAGADA_PARCIAL
            
        self.fecha_pago = datetime.now().date()

class Transaccion:
    def __init__(self, id_transaccion: str, monto: float, metodo_pago: str, factura_id: str, referencia_bancaria: str):
        self.id = id_transaccion
        self.monto = monto
        self.metodo_pago = metodo_pago
        self.factura_id = factura_id
        self.referencia_bancaria = referencia_bancaria
        self.fecha = datetime.now()
        self.estado = 'PENDIENTE'
        self.conciliado = False

    def conciliar(self):
        self.estado = 'CONCILIADA'
        self.conciliado = True
        self.fecha_conciliacion = datetime.now()

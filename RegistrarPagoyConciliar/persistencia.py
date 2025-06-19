# persistencia.py
from conexion import conectar
from datetime import date
import time

def guardar_factura(factura):
    max_intentos = 3
    intento = 0
    
    while intento < max_intentos:
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO Factura VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    factura.id, 
                    factura.pedido_id, 
                    factura.fecha_emision.isoformat(),
                    factura.total, 
                    factura.saldo_pendiente, 
                    factura.cliente,
                    factura.estado.value, 
                    factura.fecha_pago.isoformat() if factura.fecha_pago else None,
                    factura.comprobante_pago
                ))
                conn.commit()
                return
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and intento < max_intentos - 1:
                time.sleep(0.1 * (intento + 1))
                intento += 1
                continue
            raise

def guardar_transaccion(transaccion):
    max_intentos = 3
    intento = 0
    
    while intento < max_intentos:
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO Transaccion VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaccion.id,
                    transaccion.monto,
                    transaccion.metodo_pago,
                    transaccion.factura_id,
                    transaccion.referencia_bancaria,
                    transaccion.fecha.isoformat(),
                    transaccion.estado,
                    transaccion.fecha_conciliacion.isoformat() if hasattr(transaccion, 'fecha_conciliacion') else None,
                    int(transaccion.conciliado),
                    None,  # timestamp_inicio
                    None   # timestamp_fin
                ))
                conn.commit()
                return
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and intento < max_intentos - 1:
                time.sleep(0.1 * (intento + 1))
                intento += 1
                continue
            raise

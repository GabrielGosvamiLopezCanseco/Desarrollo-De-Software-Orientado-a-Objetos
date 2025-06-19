# persistencia.py
from conexion import conectar
from datetime import date
import time
import sqlite3

def guardar_factura(factura):
    
    #Guarda o actualiza una factura en la base de datos con manejo de reintentos.
    
    
    
    max_intentos = 3    # Máximo número de intentos
    intento = 0         # Contador de intentos
    
    while intento < max_intentos:
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                
                # Query SQL para insertar o reemplazar la factura
                cursor.execute("SELECT id FROM Factura WHERE id = ?", (factura.id,))
                if cursor.fetchone() is None:
                    # Insertar nueva factura
                    cursor.execute("""
                        INSERT INTO Factura VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        factura.id, 
                        factura.pedido_id,
                        factura.fecha_emision.isoformat(),  # Fecha en formato ISO
                        factura.total,
                        factura.saldo_pendiente,
                        factura.cliente,
                        factura.estado.value,  ## Valor del Enum EstadoFactura
                        factura.fecha_pago.isoformat() if factura.fecha_pago else None,
                        factura.comprobante_pago
                    ))
                else:
                    # Actualizar factura existente
                    cursor.execute("""
                        UPDATE Factura SET
                            pedido_id = ?,
                            fecha_emision = ?,
                            total = ?,
                            saldo_pendiente = ?,
                            cliente = ?,
                            estado = ?,
                            fecha_pago = ?,
                            comprobante_pago = ?
                        WHERE id = ?
                    """, (
                        factura.pedido_id,
                        factura.fecha_emision.isoformat(),
                        factura.total,
                        factura.saldo_pendiente,
                        factura.cliente,
                        factura.estado.value,
                        factura.fecha_pago.isoformat() if factura.fecha_pago else None,
                        factura.comprobante_pago,
                        factura.id
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
    
    #Guarda o actualiza una transacción de pago en la base de datos con manejo de reintentos.
    
    max_intentos = 3
    intento = 0
    
    while intento < max_intentos:
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                # Query para insertar o actualizar transacción
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
                    # Manejo condicional de fecha_conciliacion
                    transaccion.fecha_conciliacion.isoformat() if hasattr(transaccion, 'fecha_conciliacion') else None,
                    int(transaccion.conciliado),    # Convertir booleano a entero (SQLite no tiene booleano nativo)
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

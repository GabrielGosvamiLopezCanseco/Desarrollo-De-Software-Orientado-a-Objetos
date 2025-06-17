from conexion import conectar
from datetime import date  # Importación añadida

def guardar_factura(factura):
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO Factura VALUES
            (?, ?, ?, ?, ?, ?)
        """, (
            factura.id, 
            factura.pedido_id, 
            date.today().isoformat(), 
            factura.total, 
            factura.estado.value, 
            factura.fecha_pago
        ))
        conn.commit()
import sqlite3
from datetime import datetime
from modelo import Factura, Transaccion, EstadoFactura

def mostrar_tablas():
    conn = sqlite3.connect('Base_datos.db')
    cursor = conn.cursor()
    
    print("\nTablas en la base de datos:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for tabla in cursor.fetchall():
        print(f"- {tabla[0]}")
    
    conn.close()

def test_flujo_pago():
    print("\n=== TEST: Registrar Pago y Conciliar ===")
    conn = sqlite3.connect('Base_datos.db')
    cursor = conn.cursor()
    
    try:
        # 1. Insertar datos demo
        cursor.execute("INSERT OR IGNORE INTO Cliente (id, nombre) VALUES ('CLI-001', 'Cliente Demo')")
        cursor.execute("""
            INSERT OR IGNORE INTO Pedido (id, cliente_id, fecha, estado) 
            VALUES ('PED-001', 'CLI-001', date('now'), 'ENTREGADO')
        """)
        
        # 2. Crear y guardar factura (incluyendo el campo cliente)
        factura = Factura("FAC-001", "PED-001", 1500.50)
        cursor.execute("""
            INSERT INTO Factura (id, pedido_id, fecha_emision, total, cliente, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            factura.id,
            factura.pedido_id,
            datetime.now().strftime('%Y-%m-%d'),
            factura.total,
            'CLI-001',  # Valor para el campo cliente
            factura.estado.value
        ))
        
        # 3. Registrar transacción
        transaccion = Transaccion("TRX-001", 1500.50, "TRANSFERENCIA", "FAC-001")
        cursor.execute("""
            INSERT INTO Transaccion (id, monto, metodo_pago, factura_id, fecha, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            transaccion.id,
            transaccion.monto,
            transaccion.metodo_pago,
            transaccion.factura_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            transaccion.estado
        ))
        
        # 4. Marcar como pagada
        factura.marcar_como_pagada()
        cursor.execute("""
            UPDATE Factura 
            SET estado = ?, fecha_pago = ?
            WHERE id = ?
        """, (
            factura.estado.value,
            factura.fecha_pago.isoformat(),
            factura.id
        ))
        
        # 5. Conciliar
        transaccion.conciliar()
        cursor.execute("""
            UPDATE Transaccion 
            SET estado = ? 
            WHERE id = ?
        """, (transaccion.estado, transaccion.id))
        
        conn.commit()
        
        # 6. Mostrar resultados
        print("\n Datos registrados:")
        cursor.execute("SELECT id, total, estado FROM Factura WHERE id = 'FAC-001'")
        print("- Factura:", cursor.fetchone())
        
        cursor.execute("SELECT id, monto, estado FROM Transaccion WHERE id = 'TRX-001'")
        print("- Transacción:", cursor.fetchone())
        
    except Exception as e:
        conn.rollback()
        print(f"\n Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    mostrar_tablas()
    test_flujo_pago()
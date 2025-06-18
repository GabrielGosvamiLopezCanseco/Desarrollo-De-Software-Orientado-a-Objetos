# pruebas.py
import sqlite3
from datetime import datetime
from modelo import Factura, Transaccion, EstadoFactura
from persistencia import guardar_factura, guardar_transaccion

def mostrar_estructura_tablas():
    conn = None
    try:
        conn = sqlite3.connect('Base_datos.db', timeout=10)
        cursor = conn.cursor()
        
        print("\nEstructura de la tabla Factura:")
        cursor.execute("PRAGMA table_info(Factura)")
        for col in cursor.fetchall():
            print(f"{col[1]} ({col[2]})")
        
        print("\nEstructura de la tabla Transaccion:")
        cursor.execute("PRAGMA table_info(Transaccion)")
        for col in cursor.fetchall():
            print(f"{col[1]} ({col[2]})")
        
    finally:
        if conn:
            conn.close()

def configurar_datos_iniciales(conn):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO Cliente (id, nombre) VALUES ('CLI-001', 'Cliente Demo')")
    cursor.execute("""
        INSERT OR IGNORE INTO Pedido (id, cliente_id, fecha, estado) 
        VALUES ('PED-001', 'CLI-001', date('now'), 'ENTREGADO')
    """)
    conn.commit()

def test_flujo_completo():
    print("\n=== TEST: Flujo Completo ===")
    conn = None
    try:
        conn = sqlite3.connect('Base_datos.db', timeout=10)
        configurar_datos_iniciales(conn)
        
        # 1. Crear factura
        factura = Factura("FAC-001", "PED-001", 1500.50, "CLI-001")
        guardar_factura(factura)
        
        # 2. Registrar pago completo
        factura.registrar_pago(1500.50, "comprobantes/pago1.pdf")
        guardar_factura(factura)
        
        # 3. Crear transacción
        transaccion = Transaccion("TRX-001", 1500.50, "TRANSFERENCIA", "FAC-001", "REF-001")
        guardar_transaccion(transaccion)
        
        # 4. Conciliar
        transaccion.conciliar()
        guardar_transaccion(transaccion)
        
        # 5. Verificar resultados
        print("\nResultados:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.estado, f.saldo_pendiente, f.comprobante_pago,
                   t.estado, t.conciliado, t.referencia_bancaria
            FROM Factura f
            JOIN Transaccion t ON f.id = t.factura_id
            WHERE f.id = 'FAC-001'
        """)
        res = cursor.fetchone()
        print(f"Factura: {res[0]} | Estado: {res[1]} | Saldo: {res[2]}")
        print(f"Comprobante: {res[3]}")
        print(f"Transacción: Estado={res[4]} | Conciliado={res[5]} | Ref={res[6]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def test_pago_parcial():
    print("\n=== TEST: Pago Parcial ===")
    conn = None
    try:
        conn = sqlite3.connect('Base_datos.db', timeout=10)
        configurar_datos_iniciales(conn)
        
        # 1. Crear factura
        factura = Factura("FAC-002", "PED-001", 3000.00, "CLI-001")
        guardar_factura(factura)
        
        # 2. Primer pago parcial
        factura.registrar_pago(1000.00, "comprobantes/pago_parcial1.pdf")
        guardar_factura(factura)
        trans1 = Transaccion("TRX-002", 1000.00, "TARJETA", "FAC-002", "REF-002")
        guardar_transaccion(trans1)
        
        # Esperar breve momento para evitar bloqueos
        import time; time.sleep(0.1)
        
        # 3. Segundo pago parcial
        factura.registrar_pago(1500.00, "comprobantes/pago_parcial2.pdf")
        guardar_factura(factura)
        trans2 = Transaccion("TRX-003", 1500.00, "EFECTIVO", "FAC-002", "REF-003")
        guardar_transaccion(trans2)
        
        # Esperar breve momento
        time.sleep(0.1)
        
        # 4. Tercer pago (completa)
        factura.registrar_pago(500.00, "comprobantes/pago_parcial3.pdf")
        guardar_factura(factura)
        trans3 = Transaccion("TRX-004", 500.00, "TRANSFERENCIA", "FAC-002", "REF-004")
        guardar_transaccion(trans3)
        
        # 5. Conciliar
        trans1.conciliar()
        trans2.conciliar()
        trans3.conciliar()
        guardar_transaccion(trans1)
        guardar_transaccion(trans2)
        guardar_transaccion(trans3)
        
        # 6. Verificar
        cursor = conn.cursor()
        cursor.execute("SELECT estado, saldo_pendiente FROM Factura WHERE id = 'FAC-002'")
        estado, saldo = cursor.fetchone()
        print(f"\nEstado final: {estado} | Saldo: {saldo}")
        
        cursor.execute("SELECT COUNT(*) FROM Transaccion WHERE factura_id = 'FAC-002'")
        print(f"Transacciones registradas: {cursor.fetchone()[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    mostrar_estructura_tablas()
    
    # Ejecutar tests secuencialmente con pausas
    test_flujo_completo()
    import time; time.sleep(1)  # Pausa entre tests
    test_pago_parcial()

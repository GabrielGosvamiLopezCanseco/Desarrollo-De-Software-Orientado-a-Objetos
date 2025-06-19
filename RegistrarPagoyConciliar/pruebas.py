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
    
    #Configura datos básicos necesarios para las pruebas:
    # - Un cliente demo
    # - Un pedido demo
    #Args:
    #   conn: Conexión activa a la base de datos
    
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO Cliente (id, nombre) VALUES ('CLI-001', 'Cliente Demo')")
    cursor.execute("""
        INSERT OR IGNORE INTO Pedido (id, cliente_id, fecha, estado) 
        VALUES ('PED-001', 'CLI-001', date('now'), 'ENTREGADO')
    """)
    conn.commit()

def test_flujo_completo():
    #Prueba el flujo completo de:
    #1. Creación de factura
    #2. Registro de pago completo
    #3. Conciliación de transacción
    
    #Verifica que todos los estados y saldos se actualicen correctamente.
    print("\n=== TEST: Flujo Completo ===")
    conn = None
    try:
        #Configuración inicial
        conn = sqlite3.connect('Base_datos.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Factura WHERE id = 'FAC-001'")
        cursor.execute("DELETE FROM Transaccion WHERE factura_id = 'FAC-001'")
        conn.commit()
        
        configurar_datos_iniciales(conn)
        
        # 1. Crear factura
        factura = Factura("FAC-001", "PED-001", 1500.50, "CLI-001")
        guardar_factura(factura)
        
        # 2. Registrar pago completo(igual al monto total)
        factura.registrar_pago(1500.50, "comprobantes/pago1.pdf")
        guardar_factura(factura)
        
        # 3. Crear transacción asociada al pago
        transaccion = Transaccion("TRX-001", 1500.50, "TRANSFERENCIA", "FAC-001", "REF-001")
        guardar_transaccion(transaccion)
        
        # 4. Conciliar la transacción(marcar como verificada)
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
        
        #Mostrar resultados de la prueba
        print(f"Factura: {res[0]} | Estado: {res[1]} | Saldo: {res[2]}")
        print(f"Comprobante: {res[3]}")
        print(f"Transacción: Estado={res[4]} | Conciliado={res[5]} | Ref={res[6]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def test_pago_parcial():
    """
    Prueba el escenario de pagos parciales:
    1. Crea una factura con monto mayor
    2. Registra varios pagos parciales
    3. Verifica que el saldo se actualice correctamente
    4. Finalmente completa el pago y concilia
    """
    print("\n=== TEST: Pago Parcial ===")
    conn = None
    try:
        # 1. Configuración inicial con limpieza previa
        conn = sqlite3.connect('Base_datos.db', timeout=10)
        cursor = conn.cursor()
        
        # Limpiar datos de pruebas anteriores
        cursor.execute("DELETE FROM Factura WHERE id = 'FAC-002'")
        cursor.execute("DELETE FROM Transaccion WHERE factura_id = 'FAC-002'")
        conn.commit()
        
        # Configurar datos iniciales (cliente y nuevo pedido específico para esta prueba)
        cursor.execute("INSERT OR IGNORE INTO Cliente (id, nombre) VALUES ('CLI-001', 'Cliente Demo')")
        cursor.execute("""
            INSERT OR IGNORE INTO Pedido (id, cliente_id, fecha, estado) 
            VALUES ('PED-002', 'CLI-001', date('now'), 'ENTREGADO')
        """)
        conn.commit()
        
        # 2. Crear factura con nuevo pedido_id para evitar conflicto con FAC-001
        factura = Factura("FAC-002", "PED-002", 3000.00, "CLI-001")
        guardar_factura(factura)
        
        # 3. Primer pago parcial (1000 de 3000)
        factura.registrar_pago(1000.00, "comprobantes/pago_parcial1.pdf")
        guardar_factura(factura)
        trans1 = Transaccion("TRX-002", 1000.00, "TARJETA", "FAC-002", "REF-002")
        guardar_transaccion(trans1)
        
        # Pequeña pausa para evitar bloqueos
        import time; time.sleep(0.1)
        
        # 4. Segundo pago parcial (1500 de 2000 restante)
        factura.registrar_pago(1500.00, "comprobantes/pago_parcial2.pdf")
        guardar_factura(factura)
        trans2 = Transaccion("TRX-003", 1500.00, "EFECTIVO", "FAC-002", "REF-003")
        guardar_transaccion(trans2)
        
        # Pequeña pausa
        time.sleep(0.1)
        
        # 5. Tercer pago (completa el saldo de 500)
        factura.registrar_pago(500.00, "comprobantes/pago_parcial3.pdf")
        guardar_factura(factura)
        trans3 = Transaccion("TRX-004", 500.00, "TRANSFERENCIA", "FAC-002", "REF-004")
        guardar_transaccion(trans3)
        
        # 6. Conciliar todas las transacciones
        trans1.conciliar()
        trans2.conciliar()
        trans3.conciliar()
        guardar_transaccion(trans1)
        guardar_transaccion(trans2)
        guardar_transaccion(trans3)
        
        # 7. Verificación final
        cursor = conn.cursor()
        # Consultar estado final de la factura
        cursor.execute("SELECT estado, saldo_pendiente FROM Factura WHERE id = 'FAC-002'")
        estado, saldo = cursor.fetchone()
        print(f"\nEstado final: {estado} | Saldo: {saldo}")
        
        # Contar transacciones asociadas a esta factura
        cursor.execute("SELECT COUNT(*) FROM Transaccion WHERE factura_id = 'FAC-002'")
        print(f"Transacciones registradas: {cursor.fetchone()[0]}")
        
        # Mostrar detalles de las transacciones para verificación
        cursor.execute("""
            SELECT id, monto, metodo_pago, estado, referencia_bancaria 
            FROM Transaccion 
            WHERE factura_id = 'FAC-002'
        """)
        print("\nDetalles de transacciones:")
        for trx in cursor.fetchall():
            print(f"- {trx[0]}: ${trx[1]} ({trx[2]}) - {trx[3]} (Ref: {trx[4]})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    mostrar_estructura_tablas()
    
    # Ejecutar tests secuencialmente con pausas
    test_flujo_completo() #Prueba flujo completo de pago
    import time; time.sleep(1)  # Pausa entre tests
    test_pago_parcial() #Prueba pagos parciales

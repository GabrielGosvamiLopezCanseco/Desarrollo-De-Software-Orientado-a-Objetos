import sqlite3
import json

# Ruta de la base de datos
DB_PATH = r'C:\Users\GOSVA\Downloads\proyecto1\Base_datos.db'

def mostrar_negociaciones():
    try:
        # Conexión a la base de datos
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        # Consulta de las negociaciones
        cursor.execute("""
            SELECT n.id, v.nombre AS vendedor, t.nombre AS tienda, n.terminos
            FROM Negociacion n
            JOIN Vendedor v ON n.vendedor_id = v.id
            JOIN Tienda t ON n.tienda_id = t.id
        """)

        negociaciones = cursor.fetchall()

        if not negociaciones:
            print("No se encontraron negociaciones registradas.")
            return

        print("\nNegociaciones Registradas:\n")
        for neg in negociaciones:
            id_negociacion, vendedor, tienda, terminos = neg
            print(f"ID: {id_negociacion}")
            print(f"Vendedor: {vendedor}")
            print(f"Tienda: {tienda}")
            print("Términos:")

            # Decodificar los términos en formato JSON
            terminos_dict = json.loads(terminos)
            for producto in terminos_dict.get("productos", []):
                print(f"  - Producto ID: {producto['producto_id']}, Cantidad: {producto['cantidad']}")
            print(f"  Condiciones: {terminos_dict.get('condiciones', 'No especificadas')}\n")

        connection.close()
    except Exception as e:
        print(f"Error al consultar las negociaciones: {e}")

if __name__ == "__main__":
    mostrar_negociaciones()

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import psycopg2
from psycopg2 import sql, Error

class DatabaseManager:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                dbname="tienda2",  # Nombre de tu base de datos en pgAdmin
                user="postgres",    # Tu usuario de PostgreSQL
                password="0310",    # Tu contraseña
                host="localhost",
                port="5432"
            )
            self.cursor = self.connection.cursor()
            print("Conexión a PostgreSQL establecida correctamente")
            
            # Verificar y crear proveedor si no existe
            self.verificar_proveedor()
        except Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            messagebox.showerror("Error de Base de Datos", 
                               f"No se pudo conectar a la base de datos:\n{str(e)}")
            raise

    def verificar_proveedor(self):
        try:
            # Verificar si el proveedor existe
            self.cursor.execute("SELECT 1 FROM Proveedor WHERE id = 'PR001'")
            if not self.cursor.fetchone():
                # Crear el proveedor si no existe
                self.cursor.execute(
                    "INSERT INTO Proveedor (id, nombre) VALUES (%s, %s)",
                    ('PR001', 'TechDistribuidor')
                )
                print("Proveedor creado correctamente")

            # Obtener todos los productos
            self.cursor.execute("SELECT id FROM Producto")
            productos = self.cursor.fetchall()

            # Para cada producto, verificar si el proveedor tiene permiso
            for producto in productos:
                self.cursor.execute("""
                    SELECT 1 FROM Precio_Proveedor_Producto 
                    WHERE proveedor_id = 'PR001' AND producto_id = %s
                """, (producto[0],))
                
                if not self.cursor.fetchone():
                    # Si no tiene permiso, crearlo
                    self.cursor.execute("""
                        INSERT INTO Precio_Proveedor_Producto (proveedor_id, producto_id, precio)
                        VALUES (%s, %s, 0)
                    """, ('PR001', producto[0]))
                    print(f"Permiso creado para el producto {producto[0]}")

            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            print(f"Error al verificar proveedor: {e}")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            self.connection.rollback()
            print(f"Error en la consulta: {e}")
            messagebox.showerror("Error de Base de Datos", 
                               f"Error al ejecutar la consulta:\n{str(e)}")
            return False

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error en la consulta: {e}")
            messagebox.showerror("Error de Base de Datos", 
                               f"Error al obtener datos:\n{str(e)}")
            return None

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error en la consulta: {e}")
            messagebox.showerror("Error de Base de Datos", 
                               f"Error al obtener datos:\n{str(e)}")
            return []

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("Conexión a PostgreSQL cerrada correctamente")
        except Error as e:
            print(f"Error al cerrar la conexión: {e}")

class Producto:
    def __init__(self, id, nombre, precio, stock, estado):
        self.id = id
        self.nombre = nombre
        self.precio = precio
        self.stock = stock
        self.estado = estado

    @classmethod
    def from_db(cls, db_row):
        return cls(
            id=db_row[0],
            nombre=db_row[1],
            precio=db_row[2],
            stock=db_row[3],
            estado=db_row[4]
        )

class Inventario:
    def __init__(self, db_manager):
        self.db = db_manager

    def obtener_producto(self, id_producto):
        query = """
            SELECT id, nombre, precio, stock, estado
            FROM Producto
            WHERE id = %s
        """
        resultado = self.db.fetch_one(query, (id_producto,))
        return Producto.from_db(resultado) if resultado else None

    def actualizar_producto(self, id_producto, nuevo_precio, nuevo_stock, proveedor_id):
        try:
            # Verificar si el proveedor tiene permiso para este producto
            permiso_query = """
                SELECT 1 FROM Precio_Proveedor_Producto 
                WHERE producto_id = %s AND proveedor_id = %s
            """
            if not self.db.fetch_one(permiso_query, (id_producto, proveedor_id)):
                return False, "No tienes permiso para actualizar este producto"

            # Obtener valores actuales
            producto_actual = self.obtener_producto(id_producto)
            if not producto_actual:
                return False, "Producto no encontrado"

            # Iniciar transacción
            self.db.cursor.execute("BEGIN")

            # Actualizar producto
            update_query = """
                UPDATE Producto 
                SET precio = %s, stock = %s 
                WHERE id = %s
                RETURNING precio, stock
            """
            self.db.cursor.execute(update_query, (nuevo_precio, nuevo_stock, id_producto))
            updated_values = self.db.cursor.fetchone()

            if not updated_values:
                raise Exception("Producto no encontrado")

            # Registrar en historial
            historial_query = """
                INSERT INTO HistorialCambios (
                    producto_id, proveedor_id, fecha, nuevo_precio, nuevo_stock
                ) VALUES (%s, %s, %s, %s, %s)
            """
            self.db.cursor.execute(
                historial_query,
                (id_producto, proveedor_id, datetime.datetime.now(), nuevo_precio, nuevo_stock)
            )

            # Confirmar transacción
            self.db.connection.commit()
            return True, "Producto actualizado correctamente"

        except Exception as e:
            self.db.connection.rollback()
            return False, f"Error al actualizar: {str(e)}"

class Proveedor:
    def __init__(self, id, nombre, db_manager):
        self.id = id
        self.nombre = nombre
        self.db = db_manager

    def actualizar_producto(self, id_producto, nuevo_precio, nuevo_stock):
        return inventario.actualizar_producto(id_producto, nuevo_precio, nuevo_stock, self.id)

class Notificacion:
    def __init__(self, db_manager):
        self.db = db_manager

    def enviar_notificacion(self, mensaje):
        try:
            # Obtener administradores
            query = "SELECT email FROM Administrador"
            administradores = self.db.fetch_all(query)
            
            if administradores:
                for admin in administradores:
                    print(f"Notificación enviada a {admin[0]}: {mensaje}")
        except Exception as e:
            print(f"Error al enviar notificación: {e}")

class HistorialCambios:
    def __init__(self, db_manager):
        self.db = db_manager

    def obtener_historial(self):
        query = """
            SELECT h.fecha, h.producto_id, p.nombre, h.nuevo_precio, h.nuevo_stock
            FROM HistorialCambios h
            JOIN Producto p ON h.producto_id = p.id
            ORDER BY h.fecha DESC
        """
        return self.db.fetch_all(query)

class Sistema:
    def __init__(self, db_manager):
        self.db = db_manager
        self.notificacion = Notificacion(db_manager)
        self.historial = HistorialCambios(db_manager)

    def notificar_cambio(self, id_producto, precio_anterior, precio_nuevo, 
                        stock_anterior, stock_nuevo):
        mensaje = f"Cambio en producto {id_producto}:\n"
        mensaje += f"Precio: {precio_anterior} -> {precio_nuevo}\n"
        mensaje += f"Stock: {stock_anterior} -> {stock_nuevo}"
        self.notificacion.enviar_notificacion(mensaje)

class VentanaActualizarProductos:
    def __init__(self):
        self.ventana = tk.Toplevel()
        self.ventana.title("Actualizar Precios y Disponibilidad")
        self.ventana.geometry("800x600")
        
        # Frame principal
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Título
        ttk.Label(main_frame, text="Actualización de Productos", 
                 font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Frame para búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Búsqueda de Producto", padding="10")
        search_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_frame, text="ID del Producto:").grid(row=0, column=0, padx=5, pady=5)
        self.id_producto = ttk.Entry(search_frame)
        self.id_producto.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(search_frame, text="Buscar", 
                  command=self.buscar_producto).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame para actualización
        update_frame = ttk.LabelFrame(main_frame, text="Datos del Producto", padding="10")
        update_frame.pack(fill="x", pady=5)
        
        # Campos de actualización
        ttk.Label(update_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.nombre = ttk.Entry(update_frame, state="readonly")
        self.nombre.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Estado:").grid(row=1, column=0, padx=5, pady=5)
        self.estado = ttk.Entry(update_frame, state="readonly")
        self.estado.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Precio Actual:").grid(row=2, column=0, padx=5, pady=5)
        self.precio_actual = ttk.Entry(update_frame, state="readonly")
        self.precio_actual.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Nuevo Precio:").grid(row=3, column=0, padx=5, pady=5)
        self.nuevo_precio = ttk.Entry(update_frame)
        self.nuevo_precio.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Stock Actual:").grid(row=4, column=0, padx=5, pady=5)
        self.stock_actual = ttk.Entry(update_frame, state="readonly")
        self.stock_actual.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Nuevo Stock:").grid(row=5, column=0, padx=5, pady=5)
        self.nuevo_stock = ttk.Entry(update_frame)
        self.nuevo_stock.grid(row=5, column=1, padx=5, pady=5)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Actualizar", 
                  command=self.actualizar_producto).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Limpiar", 
                  command=self.limpiar_campos).pack(side="left", padx=5)
        
        # Tabla de historial
        history_frame = ttk.LabelFrame(main_frame, text="Historial de Cambios", padding="10")
        history_frame.pack(fill="both", expand=True, pady=5)
        
        # Crear Treeview para historial
        self.tree = ttk.Treeview(history_frame, 
                                columns=("Fecha", "ID", "Producto", "Precio", "Stock"),
                                show="headings")
        
        # Configurar columnas
        self.tree.heading("Fecha", text="Fecha y Hora")
        self.tree.heading("ID", text="ID Producto")
        self.tree.heading("Producto", text="Nombre Producto")
        self.tree.heading("Precio", text="Nuevo Precio")
        self.tree.heading("Stock", text="Nuevo Stock")
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar widgets
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cargar historial
        self.cargar_historial()
        
    def cargar_historial(self):
        for registro in sistema.historial.obtener_historial():
            self.tree.insert("", "end", values=registro)
    
    def buscar_producto(self):
        id_producto = self.id_producto.get()
        producto = inventario.obtener_producto(id_producto)
        
        if producto:
            self.nombre.config(state="normal")
            self.estado.config(state="normal")
            self.precio_actual.config(state="normal")
            self.stock_actual.config(state="normal")
            
            self.nombre.delete(0, "end")
            self.nombre.insert(0, producto.nombre)
            self.estado.delete(0, "end")
            self.estado.insert(0, producto.estado)
            self.precio_actual.delete(0, "end")
            self.precio_actual.insert(0, producto.precio)
            self.stock_actual.delete(0, "end")
            self.stock_actual.insert(0, producto.stock)
            
            self.nombre.config(state="readonly")
            self.estado.config(state="readonly")
            self.precio_actual.config(state="readonly")
            self.stock_actual.config(state="readonly")
        else:
            messagebox.showerror("Error", "Producto no encontrado")
    
    def actualizar_producto(self):
        try:
            id_producto = self.id_producto.get()
            nuevo_precio = float(self.nuevo_precio.get())
            nuevo_stock = int(self.nuevo_stock.get())
            
            producto = inventario.obtener_producto(id_producto)
            if producto:
                exito, mensaje = proveedor.actualizar_producto(id_producto, nuevo_precio, nuevo_stock)
                if exito:
                    sistema.notificar_cambio(
                        id_producto, producto.precio, nuevo_precio,
                        producto.stock, nuevo_stock
                    )
                    messagebox.showinfo("Éxito", mensaje)
                    self.limpiar_campos()
                    self.cargar_historial()
                else:
                    messagebox.showerror("Error", mensaje)
            else:
                messagebox.showerror("Error", "Producto no encontrado")
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores válidos")
    
    def limpiar_campos(self):
        self.id_producto.delete(0, "end")
        self.nombre.config(state="normal")
        self.estado.config(state="normal")
        self.precio_actual.config(state="normal")
        self.stock_actual.config(state="normal")
        
        self.nombre.delete(0, "end")
        self.estado.delete(0, "end")
        self.precio_actual.delete(0, "end")
        self.stock_actual.delete(0, "end")
        self.nuevo_precio.delete(0, "end")
        self.nuevo_stock.delete(0, "end")
        
        self.nombre.config(state="readonly")
        self.estado.config(state="readonly")
        self.precio_actual.config(state="readonly")
        self.stock_actual.config(state="readonly")

# Inicialización de objetos globales
db_manager = DatabaseManager()
inventario = Inventario(db_manager)
sistema = Sistema(db_manager)
proveedor = Proveedor("PR001", "TechDistribuidor", db_manager)

def ejecutar():
    try:
        ventana = VentanaActualizarProductos()
        ventana.ventana.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Error al iniciar la aplicación:\n{str(e)}")
    finally:
        if 'db_manager' in globals():
            db_manager.close()
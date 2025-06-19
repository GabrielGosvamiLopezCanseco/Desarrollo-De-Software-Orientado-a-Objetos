import sqlite3
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

# Ruta de la base de datos (ajusta según tu estructura de archivos)
DB_PATH = 'Base_datos.db'

class NegociacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Negociar con Tiendas Departamentales")
        self.root.geometry("500x400")

        # Variables para almacenar selecciones
        self.tienda_seleccionada = tk.StringVar()
        self.vendedor_seleccionado = tk.StringVar()
        
        # Contenedor principal
        frame_principal = tk.Frame(root, padx=10, pady=10)
        frame_principal.pack(fill=tk.BOTH, expand=True)

        # Frame para tienda
        frame_tienda = tk.LabelFrame(frame_principal, text="Seleccionar Tienda", padx=5, pady=5)
        frame_tienda.pack(fill=tk.X, pady=5)
        
        self.menu_tienda = tk.OptionMenu(frame_tienda, self.tienda_seleccionada, "")
        self.menu_tienda.pack(fill=tk.X)

        # Frame para vendedor
        frame_vendedor = tk.LabelFrame(frame_principal, text="Seleccionar Vendedor", padx=5, pady=5)
        frame_vendedor.pack(fill=tk.X, pady=5)
        
        self.menu_vendedor = tk.OptionMenu(frame_vendedor, self.vendedor_seleccionado, "")
        self.menu_vendedor.pack(fill=tk.X)

        # Frame para productos
        frame_productos = tk.LabelFrame(frame_principal, text="Seleccionar Productos", padx=5, pady=5)
        frame_productos.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(frame_productos)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lista_productos = tk.Listbox(
            frame_productos, 
            selectmode=tk.MULTIPLE, 
            yscrollcommand=scrollbar.set,
            height=8
        )
        self.lista_productos.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.lista_productos.yview)

        # Botón de acción
        tk.Button(
            frame_principal, 
            text="Registrar Negociación", 
            command=self.registrar_negociacion,
            bg="#4CAF50",
            fg="white"
        ).pack(pady=10)

        # Cargar datos iniciales
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self):
        """Carga tiendas, vendedores y productos al iniciar la aplicación"""
        self.actualizar_menu_tiendas()
        self.actualizar_menu_vendedores()
        self.cargar_productos()

    def actualizar_menu_tiendas(self):
        """Actualiza el menú de tiendas con datos de la base de datos"""
        try:
            menu = self.menu_tienda["menu"]
            menu.delete(0, "end")
            
            tiendas = self.obtener_datos_tabla("Tienda")
            if not tiendas:
                messagebox.showwarning("Advertencia", "No hay tiendas registradas")
                return
            
            for tienda in tiendas:
                menu.add_command(
                    label=f"{tienda['id']} - {tienda['nombre']}",
                    command=lambda v=tienda['id']: [
                        self.tienda_seleccionada.set(v),
                        self.actualizar_menu_vendedores()
                    ]
                )
            
            # Establecer primer valor por defecto
            if tiendas:
                self.tienda_seleccionada.set(tiendas[0]['id'])

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las tiendas: {str(e)}")

    def actualizar_menu_vendedores(self):
        """Actualiza el menú de vendedores con datos de la base de datos"""
        try:
            menu = self.menu_vendedor["menu"]
            menu.delete(0, "end")
            
            vendedores = self.obtener_datos_tabla("Vendedor")
            if not vendedores:
                messagebox.showwarning("Advertencia", "No hay vendedores registrados")
                return
            
            for vendedor in vendedores:
                menu.add_command(
                    label=f"{vendedor['id']} - {vendedor['nombre']}",
                    command=lambda v=vendedor['id']: self.vendedor_seleccionado.set(v)
                )
            
            # Establecer primer valor por defecto
            if vendedores:
                self.vendedor_seleccionado.set(vendedores[0]['id'])

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los vendedores: {str(e)}")

    def obtener_datos_tabla(self, tabla):
        """Obtiene datos de una tabla específica"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f"SELECT id, nombre FROM {tabla}")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener datos de {tabla}: {str(e)}")
            return []

    def cargar_productos(self):
        """Carga los productos disponibles en la lista"""
        try:
            self.lista_productos.delete(0, tk.END)
            
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, precio, stock FROM Producto")
                
                for producto in cursor.fetchall():
                    self.lista_productos.insert(
                        tk.END, 
                        f"{producto[0]} - {producto[1]} - ${producto[2]:.2f} - Stock: {producto[3]}"
                    )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {str(e)}")

    def registrar_negociacion(self):
        """Registra una nueva negociación en la base de datos y actualiza el stock"""
        try:
            # Validar selecciones
            if not self.tienda_seleccionada.get():
                messagebox.showerror("Error", "Debe seleccionar una tienda")
                return
                
            if not self.vendedor_seleccionado.get():
                messagebox.showerror("Error", "Debe seleccionar un vendedor")
                return
                
            productos_seleccionados = self.lista_productos.curselection()
            if not productos_seleccionados:
                messagebox.showerror("Error", "Debe seleccionar al menos un producto")
                return

            # Procesar productos seleccionados
            productos = []
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                for index in productos_seleccionados:
                    item = self.lista_productos.get(index)
                    partes = item.split(" - ")
                    
                    if len(partes) < 4:
                        continue  # Saltar elementos mal formados
                        
                    producto_id = partes[0]
                    stock = int(partes[3].split(": ")[1])
                    
                    cantidad = simpledialog.askinteger(
                        "Cantidad",
                        f"Ingrese cantidad para {partes[1]} (Stock: {stock}):",
                        parent=self.root,
                        minvalue=1,
                        maxvalue=stock
                    )
                    
                    if not cantidad:  # Usuario canceló
                        return
                        
                    # Agregar producto a la negociación
                    productos.append({
                        "producto_id": producto_id,
                        "nombre": partes[1],
                        "precio": float(partes[2][1:]),  # Eliminar $
                        "cantidad": cantidad,
                        "stock_actual": stock
                    })

                    # Actualizar el stock del producto
                    nuevo_stock = stock - cantidad
                    cursor.execute(
                        "UPDATE Producto SET stock = ? WHERE id = ?",
                        (nuevo_stock, producto_id)
                    )

                # Crear términos de negociación
                terminos = {
                    "productos": productos,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "estado": "Pendiente"
                }

                # Insertar en la base de datos
                cursor.execute(
                    "INSERT INTO Negociacion (vendedor_id, tienda_id, terminos) VALUES (?, ?, ?)",
                    (self.vendedor_seleccionado.get(), self.tienda_seleccionada.get(), json.dumps(terminos))
                )
                conn.commit()

            messagebox.showinfo("Éxito", "Negociación registrada correctamente y stock actualizado")
            self.lista_productos.selection_clear(0, tk.END)  # Limpiar selección
            self.cargar_productos()  # Refrescar lista de productos

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la negociación: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NegociacionApp(root)
    root.mainloop()     
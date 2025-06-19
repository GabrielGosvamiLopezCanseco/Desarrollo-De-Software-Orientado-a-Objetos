import tkinter as tk
from tkinter import messagebox
from conexion import conectar
from datetime import date
import uuid

# Obtener productos activos
def obtener_productos_activos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, precio FROM Producto WHERE estado = 'ACTIVO'")
    productos = cur.fetchall()
    conn.close()
    return productos

# Crear pedido con más datos
def crear_pedido(cliente_id, producto_id, cantidad, direccion, tipo, observaciones):
    conn = conectar()
    cur = conn.cursor()
    pedido_id = str(uuid.uuid4())
    hoy = date.today()

    # Insertar el pedido con datos nuevos
    cur.execute("""
        INSERT INTO Pedido (id, cliente_id, fecha, estado, direccion_entrega, tipo_pedido, observaciones)
        VALUES (%s, %s, %s, 'PENDIENTE', %s, %s, %s)
    """, (pedido_id, cliente_id, hoy, direccion, tipo, observaciones))

    cur.execute("INSERT INTO Pedido_Producto (pedido_id, producto_id, cantidad) VALUES (%s, %s, %s)",
                (pedido_id, producto_id, cantidad))

    conn.commit()
    conn.close()
    return pedido_id

# Consultar pedidos por cliente
def consultar_pedidos(cliente_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT P.id, P.fecha, P.estado, PR.nombre, PP.cantidad, P.tipo_pedido, P.direccion_entrega, P.observaciones
        FROM Pedido P
        JOIN Pedido_Producto PP ON P.id = PP.pedido_id
        JOIN Producto PR ON PP.producto_id = PR.id
        WHERE P.cliente_id = %s
        ORDER BY P.fecha DESC
    """, (cliente_id,))
    resultados = cur.fetchall()
    conn.close()
    return resultados

# Crear interfaz
ventana = tk.Tk()
ventana.title("Cliente Empresa - Tienda Mayorista")
ventana.geometry("600x600")

tk.Label(ventana, text="ID del Cliente:").pack()
cliente_entry = tk.Entry(ventana)
cliente_entry.pack()

productos = obtener_productos_activos()
producto_var = tk.StringVar()
tk.Label(ventana, text="Selecciona un Producto:").pack()
producto_menu = tk.OptionMenu(ventana, producto_var, *[
    f"{p[0]} - {p[1]} - ${p[2]}" for p in productos
])
producto_menu.pack()

tk.Label(ventana, text="Cantidad:").pack()
cantidad_entry = tk.Entry(ventana)
cantidad_entry.pack()

tk.Label(ventana, text="Dirección de Entrega:").pack()
direccion_entry = tk.Entry(ventana, width=50)
direccion_entry.pack()

tk.Label(ventana, text="Tipo de Pedido:").pack()
tipo_var = tk.StringVar()
tipo_menu = tk.OptionMenu(ventana, tipo_var, "Regular", "Urgente", "Programado")
tipo_menu.pack()

tk.Label(ventana, text="Observaciones (opcional):").pack()
observaciones_entry = tk.Entry(ventana, width=50)
observaciones_entry.pack()

def accion_realizar_pedido():
    cliente_id = cliente_entry.get().strip()
    cantidad = cantidad_entry.get().strip()
    prod_str = producto_var.get()
    direccion = direccion_entry.get().strip()
    tipo = tipo_var.get().strip()
    observaciones = observaciones_entry.get().strip()

    if not cliente_id or not cantidad.isdigit() or not prod_str or not direccion or not tipo:
        messagebox.showerror("Error", "Completa todos los campos obligatorios.")
        return

    producto_id = prod_str.split(" - ")[0]
    pedido_id = crear_pedido(cliente_id, producto_id, int(cantidad), direccion, tipo, observaciones)
    messagebox.showinfo("Éxito", f"Pedido registrado con ID: {pedido_id}")

def accion_consultar_pedidos():
    cliente_id = cliente_entry.get().strip()
    pedidos = consultar_pedidos(cliente_id)

    if not pedidos:
        messagebox.showinfo("Sin resultados", "No hay pedidos para este cliente.")
        return

    mensaje = ""
    for pid, fecha, estado, prod, cant, tipo, direccion, obs in pedidos:
        mensaje += f"ID: {pid}\nFecha: {fecha}\nProducto: {prod} x{cant}\nEstado: {estado}\n"
        mensaje += f"Tipo: {tipo}\nEntrega: {direccion}\nObs: {obs or 'N/A'}\n\n"
    messagebox.showinfo("Pedidos", mensaje)

tk.Button(ventana, text="Realizar Pedido", command=accion_realizar_pedido).pack(pady=10)
tk.Button(ventana, text="Consultar Pedidos", command=accion_consultar_pedidos).pack(pady=5)

ventana.mainloop()
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

# Crear pedido y registrar en la base
def crear_pedido(cliente_id, producto_id, cantidad):
    conn = conectar()
    cur = conn.cursor()
    pedido_id = str(uuid.uuid4())
    hoy = date.today()

    cur.execute("INSERT INTO Pedido (id, cliente_id, fecha, estado) VALUES (%s, %s, %s, 'PENDIENTE')",
                (pedido_id, cliente_id, hoy))
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
        SELECT P.id, P.fecha, P.estado, PR.nombre, PP.cantidad
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
ventana.geometry("500x400")

tk.Label(ventana, text="ID del Cliente:").pack()
cliente_entry = tk.Entry(ventana)
cliente_entry.pack()

productos = obtener_productos_activos()
producto_var = tk.StringVar()
producto_menu = tk.OptionMenu(ventana, producto_var, *[
    f"{p[0]} - {p[1]} - ${p[2]}" for p in productos
])
producto_menu.pack()

tk.Label(ventana, text="Cantidad:").pack()
cantidad_entry = tk.Entry(ventana)
cantidad_entry.pack()

def accion_realizar_pedido():
    cliente_id = cliente_entry.get().strip()
    cantidad = cantidad_entry.get().strip()
    prod_str = producto_var.get()

    if not cliente_id or not cantidad.isdigit() or not prod_str:
        messagebox.showerror("Error", "Completa todos los campos correctamente.")
        return

    producto_id = prod_str.split(" - ")[0]
    pedido_id = crear_pedido(cliente_id, producto_id, int(cantidad))
    messagebox.showinfo("Éxito", f"Pedido registrado con ID: {pedido_id}")

def accion_consultar_pedidos():
    cliente_id = cliente_entry.get().strip()
    pedidos = consultar_pedidos(cliente_id)

    if not pedidos:
        messagebox.showinfo("Sin resultados", "No hay pedidos para este cliente.")
        return

    mensaje = ""
    for pid, fecha, estado, prod, cant in pedidos:
        mensaje += f"{fecha} - {prod} x{cant} → {estado}\n"
    messagebox.showinfo("Pedidos", mensaje)

tk.Button(ventana, text="Realizar Pedido", command=accion_realizar_pedido).pack(pady=10)
tk.Button(ventana, text="Consultar Pedidos", command=accion_consultar_pedidos).pack(pady=5)

ventana.mainloop()
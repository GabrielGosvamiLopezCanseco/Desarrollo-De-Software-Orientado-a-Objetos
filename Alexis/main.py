import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import os
import actualizar_productos
import generar_factura

class Aplicacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Productos")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # Estilo
        style = ttk.Style()
        style.configure("Custom.TButton", padding=10, font=('Helvetica', 12))

        # Frame principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(expand=True, fill="both")

        # Título
        titulo = ttk.Label(main_frame, text="Sistema de Gestión de Productos", 
                          font=('Helvetica', 16, 'bold'))
        titulo.pack(pady=20)

        # Frame para los botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(expand=True)

        # Botones de casos de uso
        botones = [
            ("Actualizar Productos", self.actualizar_productos),
            ("Ver Historial", self.ver_historial),
            ("Generar Factura", self.generar_factura),
            ("Generar Reportes", self.generar_reportes),
            ("Configuración", self.configuracion),
            ("Salir", self.salir)
        ]

        for i, (texto, comando) in enumerate(botones):
            btn = ttk.Button(button_frame, text=texto, command=comando, 
                           style="Custom.TButton", width=25)
            btn.grid(row=i//2, column=i%2, padx=10, pady=10)

    def actualizar_productos(self):
        try:
            actualizar_productos.ejecutar()
        except ImportError:
            messagebox.showerror("Error", "No se pudo cargar el módulo de actualización de productos")
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar la actualización de productos: {str(e)}")

    def ver_historial(self):
        try:
            # Implementar apertura de historial
            pass
        except ImportError:
            messagebox.showerror("Error", "No se pudo cargar el módulo de historial")

    def generar_factura(self):
        try:
            generar_factura.ejecutar()
        except ImportError:
            messagebox.showerror("Error", "No se pudo cargar el módulo de generación de factura")

    def generar_reportes(self):
        try:
            # Implementar apertura de reportes
            pass
        except ImportError:
            messagebox.showerror("Error", "No se pudo cargar el módulo de reportes")

    def configuracion(self):
        try:
            # Implementar apertura de configuración
            pass
        except ImportError:
            messagebox.showerror("Error", "No se pudo cargar el módulo de configuración")

    def salir(self):
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir?"):
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplicacion(root)
    root.mainloop()




import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import psycopg2
from psycopg2 import sql, Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import os
from decimal import Decimal
import logging
import traceback
from typing import Dict, List, Optional, Tuple, Union
import time
from email.mime.base import MIMEBase
from email import encoders
import webbrowser
import urllib.parse

# Usuario por defecto (simulando que ya está logueado)
USUARIO_ACTUAL = {
    'id': 'U001',
    'nombre': 'Luis Torres',
    'rol': 'ADMINISTRADOR'
}

# Configuración de logging más detallada
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para más detalles
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facturacion.log', mode='w'),  # Modo 'w' para sobrescribir el archivo
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de email (puedes cambiar estos valores)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_remitente': 'tu_email@gmail.com',
    'password': 'tu_password_app',  # Contraseña de aplicación de Gmail
    'nombre_empresa': 'Tu Empresa S.A. de C.V.'
}

class DatabaseManager:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                dbname="tienda2",
                user="postgres",
                password="0310",
                host="localhost",
                port="5432"
            )
            self.cursor = self.connection.cursor()
            print("Conexión a la base de datos establecida")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Conexión a la base de datos cerrada")

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error al ejecutar consulta: {e}")
            raise

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error al ejecutar consulta: {e}")
            raise

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Error al ejecutar consulta: {e}")
            raise

class Cliente:
    def __init__(self, id: str, nombre: str, direccion: str, rfc: str, 
                 regimen_fiscal: str, direccion_fiscal: str):
        self.id = id
        self.nombre = nombre
        self.direccion = direccion
        self.rfc = rfc
        self.regimen_fiscal = regimen_fiscal
        self.direccion_fiscal = direccion_fiscal

    @classmethod
    def from_db(cls, db: DatabaseManager, cliente_id: str) -> Optional['Cliente']:
        try:
            db.cursor.execute("""
                SELECT id, nombre, direccion, rfc, regimen_fiscal, direccion_fiscal
                FROM Cliente WHERE id = %s
            """, (cliente_id,))
            row = db.cursor.fetchone()
            if row:
                return cls(*row)
            return None
        except Exception as e:
            logger.error(f"Error al obtener cliente: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Producto:
    def __init__(self, id: str, nombre: str, precio: Decimal, stock: int, estado: str):
        self.id = id
        self.nombre = nombre
        self.precio = precio
        self.stock = stock
        self.estado = estado

    @classmethod
    def from_db(cls, db: DatabaseManager, producto_id: str) -> Optional['Producto']:
        try:
            db.cursor.execute("""
                SELECT id, nombre, precio, stock, estado
                FROM Producto WHERE id = %s
            """, (producto_id,))
            row = db.cursor.fetchone()
            if row:
                return cls(*row)
            return None
        except Exception as e:
            logger.error(f"Error al obtener producto: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Pedido:
    def __init__(self, id: str, cliente_id: str, fecha: datetime, estado: str):
        self.id = id
        self.cliente_id = cliente_id
        self.fecha = fecha
        self.estado = estado
        self.productos: List[Tuple[Producto, int]] = []

    @classmethod
    def from_db(cls, db: DatabaseManager, pedido_id: str) -> Optional['Pedido']:
        try:
            # Obtener datos del pedido
            db.cursor.execute("""
                SELECT id, cliente_id, fecha, estado
                FROM Pedido WHERE id = %s
            """, (pedido_id,))
            row = db.cursor.fetchone()
            if not row:
                return None

            pedido = cls(*row)

            # Obtener productos del pedido
            db.cursor.execute("""
                SELECT p.id, p.nombre, p.precio, p.stock, p.estado, pp.cantidad
                FROM Pedido_Producto pp
                JOIN Producto p ON pp.producto_id = p.id
                WHERE pp.pedido_id = %s
            """, (pedido_id,))
            
            for row in db.cursor.fetchall():
                producto = Producto(*row[:5])
                cantidad = row[5]
                pedido.productos.append((producto, cantidad))

            return pedido
        except Exception as e:
            logger.error(f"Error al obtener pedido: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Factura:
    def __init__(self, id: str, pedido_id: str, subtotal: Decimal, iva: Decimal, total: Decimal):
        self.id = id
        self.pedido_id = pedido_id
        self.fecha_emision = datetime.datetime.now()
        self.subtotal = subtotal
        self.iva = iva
        self.total = total
        self.estatus = 'ACTIVA'  # Valor por defecto

    @classmethod
    def from_db(cls, db: DatabaseManager, factura_id: str) -> Optional['Factura']:
        try:
            db.cursor.execute("""
                SELECT id, pedido_id, fecha_emision, subtotal, iva, total, estatus
                FROM Factura WHERE id = %s
            """, (factura_id,))
            row = db.cursor.fetchone()
            if row:
                return cls(*row)
            return None
        except Exception as e:
            logger.error(f"Error al obtener factura: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def generar_cfdi(self, db: DatabaseManager) -> str:
        try:
            # Obtener datos del pedido y cliente
            pedido = Pedido.from_db(db, self.pedido_id)
            if not pedido:
                raise ValueError("Pedido no encontrado")

            cliente = Cliente.from_db(db, pedido.cliente_id)
            if not cliente:
                raise ValueError("Cliente no encontrado")

            # Obtener parámetros del sistema
            params = db.get_parametros_sistema()
            
            # Generar XML del CFDI
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
                  Version="4.0"
                  Serie="A"
                  Folio="{self.id}"
                  Fecha="{self.fecha_emision.strftime('%Y-%m-%dT%H:%M:%S')}"
                  Sello=""
                  NoCertificado=""
                  Certificado=""
                  SubTotal="{self.subtotal}"
                  Moneda="MXN"
                  Total="{self.total}"
                  TipoDeComprobante="I"
                  Exportacion="01"
                  MetodoPago="PPD"
                  FormaPago="99"
                  LugarExpedicion="12345">
    <cfdi:Emisor Rfc="{params.get('rfc_emisor', '')}"
                 Nombre="{params.get('nombre_emisor', '')}"
                 RegimenFiscal="{params.get('regimen_fiscal', '')}"/>
    <cfdi:Receptor Rfc="{cliente.rfc}"
                   Nombre="{cliente.nombre}"
                   RegimenFiscal="{cliente.regimen_fiscal}"
                   DomicilioFiscalReceptor="{cliente.direccion_fiscal}"
                   UsoCFDI="G03"/>
    <cfdi:Conceptos>
"""
            
            # Agregar conceptos
            for producto, cantidad in pedido.productos:
                xml += f"""        <cfdi:Concepto ClaveProdServ="01010101"
                           Cantidad="{cantidad}"
                           ClaveUnidad="H87"
                           Descripcion="{producto.nombre}"
                           ValorUnitario="{producto.precio}"
                           Importe="{producto.precio * cantidad}">
            <cfdi:Impuestos>
                <cfdi:Traslados>
                    <cfdi:Traslado Base="{producto.precio * cantidad}"
                                  Impuesto="002"
                                  TipoFactor="Tasa"
                                  TasaOCuota="0.160000"
                                  Importe="{producto.precio * cantidad * Decimal('0.16')}"/>
                </cfdi:Traslados>
            </cfdi:Impuestos>
        </cfdi:Concepto>
"""
            
            xml += """    </cfdi:Conceptos>
    <cfdi:Impuestos TotalImpuestosTrasladados="0.00">
        <cfdi:Traslados>
            <cfdi:Traslado Impuesto="002"
                          TipoFactor="Tasa"
                          TasaOCuota="0.160000"
                          Importe="0.00"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>
</cfdi:Comprobante>"""

            # Guardar XML
            filename = f"facturas/{self.id}.xml"
            os.makedirs("facturas", exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(xml)

            logger.info(f"CFDI generado exitosamente: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error al generar CFDI: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def guardar(self, db: DatabaseManager) -> bool:
        try:
            # Verificar si ya existe una factura para este pedido
            db.cursor.execute("""
                SELECT 1 FROM Factura WHERE pedido_id = %s
            """, (self.pedido_id,))
            
            if db.cursor.fetchone():
                raise ValueError("Ya existe una factura para este pedido")

            # Insertar factura
            db.cursor.execute("""
                INSERT INTO Factura (id, pedido_id, fecha_emision, total, estatus)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.id, self.pedido_id, self.fecha_emision, self.total, self.estatus))

            # Actualizar estado del pedido
            db.cursor.execute("""
                UPDATE Pedido SET estado = 'FACTURADO'
                WHERE id = %s
            """, (self.pedido_id,))

            # Registrar en cuenta por cobrar
            db.cursor.execute("""
                INSERT INTO CuentaPorCobrar (factura_id, fecha_emision, monto)
                VALUES (%s, %s, %s)
            """, (self.id, self.fecha_emision, self.total))

            db.connection.commit()
            return True

        except Exception as e:
            db.connection.rollback()
            logger.error(f"Error al guardar factura: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Impuesto:
    def __init__(self, id: int, nombre: str, tasa: Decimal):
        self.id = id
        self.nombre = nombre
        self.tasa = tasa

    @classmethod
    def from_db(cls, db: DatabaseManager) -> List['Impuesto']:
        try:
            impuestos = []
            for imp_data in db.get_impuestos():
                impuestos.append(cls(
                    id=imp_data['id'],
                    nombre=imp_data['nombre'],
                    tasa=imp_data['tasa']
                ))
            return impuestos
        except Exception as e:
            logger.error(f"Error al obtener impuestos: {str(e)}")
            raise

class Sistema:
    def __init__(self, db_manager):
        self.db = db_manager
        self.impuesto = Impuesto.from_db(db_manager)[0]

    def validar_datos_fiscales(self, cliente):
        # Validación básica de RFC (13 caracteres para personas físicas, 12 para morales)
        if not (len(cliente.rfc) in [12, 13]):
            return False, "RFC inválido"
        
        # Validación básica de dirección fiscal
        if not cliente.direccion_fiscal or len(cliente.direccion_fiscal) < 10:
            return False, "Dirección fiscal incompleta"
        
        # Validación básica de régimen fiscal
        if not cliente.regimen_fiscal:
            return False, "Régimen fiscal no especificado"
        
        return True, "Datos fiscales válidos"

    def enviar_factura_email(self, cliente, factura_pdf):
        try:
            # Configuración del servidor SMTP (ejemplo con Gmail)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "tu_correo@gmail.com"  # Reemplazar con el correo real
            sender_password = "tu_contraseña"     # Reemplazar con la contraseña real

            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = cliente.email
            msg['Subject'] = f"Factura Electrónica #{factura_pdf.id}"

            # Cuerpo del mensaje
            body = f"""
            Estimado/a {cliente.nombre},

            Adjunto encontrará su factura electrónica #{factura_pdf.id}.

            Saludos cordiales,
            Sistema de Facturación
            """
            msg.attach(MIMEText(body, 'plain'))

            # Adjuntar PDF
            with open(factura_pdf, 'rb') as f:
                pdf = MIMEApplication(f.read(), _subtype='pdf')
                pdf.add_header('Content-Disposition', 'attachment', filename=f'factura_{factura_pdf.id}.pdf')
                msg.attach(pdf)

            # Enviar email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True, "Factura enviada correctamente"
        except Exception as e:
            return False, f"Error al enviar factura: {str(e)}"

class FacturaManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_pedidos_pendientes(self):
        try:
            query = """
                SELECT p.id, p.fecha, c.nombre as cliente_nombre, c.rfc, c.regimen_fiscal
                FROM Pedido p
                JOIN Cliente c ON p.cliente_id = c.id
                WHERE p.estado = 'ENTREGADO'
                AND NOT EXISTS (
                    SELECT 1 FROM Factura f WHERE f.pedido_id = p.id
                )
                ORDER BY p.fecha DESC
            """
            return self.db.fetch_all(query)
        except Exception as e:
            print(f"Error al obtener pedidos pendientes: {e}")
            raise

    def get_detalle_pedido(self, pedido_id):
        try:
            query = """
                SELECT p.id, p.nombre, p.precio, pp.cantidad
                FROM Pedido_Producto pp
                JOIN Producto p ON pp.producto_id = p.id
                WHERE pp.pedido_id = %s
            """
            return self.db.fetch_all(query, (pedido_id,))
        except Exception as e:
            print(f"Error al obtener detalle del pedido: {e}")
            raise

    def generar_factura(self, pedido_id, subtotal, iva, total, usuario_id):
        try:
            # Generar ID de factura
            self.db.cursor.execute("SELECT nextval('factura_id_seq')")
            factura_id = f"F{self.db.cursor.fetchone()[0]:06d}"

            # Insertar factura
            query = """
                INSERT INTO Factura (id, pedido_id, fecha_emision, subtotal, iva, total, estatus)
                VALUES (%s, %s, %s, %s, %s, %s, 'EMITIDA')
                RETURNING id
            """
            self.db.execute(query, (factura_id, pedido_id, datetime.now().date(), 
                                  subtotal, iva, total))

            # Crear cuenta por cobrar
            query = """
                INSERT INTO CuentaPorCobrar (factura_id, cliente_id, fecha_emision, monto, estatus)
                SELECT %s, p.cliente_id, %s, %s, 'PENDIENTE'
                FROM Pedido p WHERE p.id = %s
            """
            self.db.execute(query, (factura_id, datetime.now().date(), total, pedido_id))

            return factura_id
        except Exception as e:
            print(f"Error al generar factura: {e}")
            raise

class GenerarFacturaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generar Factura")
        self.root.geometry("800x600")
        
        # Hacer que la ventana se mantenga arriba de la ventana principal
        self.root.attributes('-topmost', True)
        
        # Inicializar variables
        self.db = DatabaseManager()
        self.factura_manager = FacturaManager(self.db)
        self.pedido_seleccionado = None
        self.subtotal = Decimal('0.00')
        self.iva = Decimal('0.00')
        self.total = Decimal('0.00')
        
        # Crear widgets
        self.crear_widgets()
        
        # Cargar pedidos pendientes
        self.cargar_pedidos_pendientes()

    def crear_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sección de selección de pedido
        pedido_frame = ttk.LabelFrame(main_frame, text="Seleccionar Pedido", padding="5")
        pedido_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.pedido_combobox = ttk.Combobox(pedido_frame, state="readonly", width=50)
        self.pedido_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.pedido_combobox.bind("<<ComboboxSelected>>", self.on_pedido_selected)
        
        # Botón de refrescar
        ttk.Button(pedido_frame, text="Refrescar", 
                  command=self.cargar_pedidos_pendientes).grid(row=0, column=1, padx=5)
        
        # Sección de datos del cliente
        cliente_frame = ttk.LabelFrame(main_frame, text="Datos del Cliente", padding="5")
        cliente_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(cliente_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W)
        self.cliente_label = ttk.Label(cliente_frame, text="")
        self.cliente_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(cliente_frame, text="RFC:").grid(row=1, column=0, sticky=tk.W)
        self.rfc_label = ttk.Label(cliente_frame, text="")
        self.rfc_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(cliente_frame, text="Regimen Fiscal:").grid(row=2, column=0, sticky=tk.W)
        self.regimen_label = ttk.Label(cliente_frame, text="")
        self.regimen_label.grid(row=2, column=1, sticky=tk.W)
        
        # Sección de productos
        productos_frame = ttk.LabelFrame(main_frame, text="Productos", padding="5")
        productos_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Treeview para productos
        self.tree = ttk.Treeview(productos_frame, 
                               columns=("nombre", "cantidad", "precio", "subtotal"), 
                               show="headings", 
                               height=6)
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("precio", text="Precio")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("nombre", width=200, anchor=tk.CENTER)
        self.tree.column("cantidad", width=100, anchor=tk.CENTER)
        self.tree.column("precio", width=150, anchor=tk.E)
        self.tree.column("subtotal", width=150, anchor=tk.E)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(productos_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Sección de totales
        totales_frame = ttk.LabelFrame(main_frame, text="Totales", padding="5")
        totales_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(totales_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.W)
        self.subtotal_label = ttk.Label(totales_frame, text="$0.00")
        self.subtotal_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(totales_frame, text="IVA:").grid(row=1, column=0, sticky=tk.W)
        self.iva_label = ttk.Label(totales_frame, text="$0.00")
        self.iva_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(totales_frame, text="Total:").grid(row=2, column=0, sticky=tk.W)
        self.total_label = ttk.Label(totales_frame, text="$0.00")
        self.total_label.grid(row=2, column=1, sticky=tk.W)
        
        # Botones
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.generar_button = ttk.Button(botones_frame, 
                                       text="Generar Factura", 
                                       command=self.generar_factura)
        self.generar_button.grid(row=0, column=0, padx=5)
        
        self.cancelar_button = ttk.Button(botones_frame, 
                                        text="Cancelar", 
                                        command=self.on_closing)
        self.cancelar_button.grid(row=0, column=1, padx=5)
        
        # Configurar expansión de widgets
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        productos_frame.columnconfigure(0, weight=1)

    def cargar_pedidos_pendientes(self):
        try:
            pedidos = self.factura_manager.get_pedidos_pendientes()
            if not pedidos:
                # Crear una ventana de mensaje personalizada que se mantenga arriba
                self.mostrar_mensaje_sin_pedidos()
                return
                
            self.pedido_combobox['values'] = [
                f"{p[0]} - {p[2]} ({p[1]})" 
                for p in pedidos
            ]
            self.pedido_combobox.set(self.pedido_combobox['values'][0])
            self.on_pedido_selected(None)
            
        except Exception as e:
            # Crear una ventana de mensaje personalizada para errores
            self.mostrar_mensaje_error(f"Error al cargar los pedidos pendientes:\n{str(e)}")

    def mostrar_mensaje_sin_pedidos(self):
        """Muestra un mensaje personalizado cuando no hay pedidos pendientes"""
        # Crear ventana de mensaje
        mensaje_window = tk.Toplevel(self.root)
        mensaje_window.title("Información")
        mensaje_window.geometry("400x200")
        mensaje_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        mensaje_window.attributes('-topmost', True)
        mensaje_window.transient(self.root)
        mensaje_window.grab_set()
        
        # Centrar la ventana
        mensaje_window.update_idletasks()
        x = (mensaje_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (mensaje_window.winfo_screenheight() // 2) - (200 // 2)
        mensaje_window.geometry(f"400x200+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(mensaje_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de información
        info_label = tk.Label(main_frame, text="ℹ️", font=('Arial', 24), bg='white')
        info_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text="No hay pedidos pendientes de facturación.\n\nTodos los pedidos ya han sido facturados\no no hay pedidos entregados.",
                                font=('Arial', 12), 
                                bg='white',
                                justify=tk.CENTER)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        def cerrar_mensaje():
            mensaje_window.destroy()
            # Limpiar el combobox
            self.pedido_combobox['values'] = []
            self.pedido_combobox.set('')
            # Limpiar los campos
            self.limpiar_campos()
        
        tk.Button(main_frame, text="Aceptar", 
                 command=cerrar_mensaje,
                 bg='#4CAF50', fg='white', font=('Arial', 12)).pack()

    def mostrar_mensaje_error(self, mensaje):
        """Muestra un mensaje de error personalizado"""
        # Crear ventana de error
        error_window = tk.Toplevel(self.root)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        error_window.attributes('-topmost', True)
        error_window.transient(self.root)
        error_window.grab_set()
        
        # Centrar la ventana
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (error_window.winfo_screenheight() // 2) - (200 // 2)
        error_window.geometry(f"400x200+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(error_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de error
        error_label = tk.Label(main_frame, text="❌", font=('Arial', 24), bg='white')
        error_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text=mensaje,
                                font=('Arial', 12), 
                                bg='white',
                                justify=tk.CENTER)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        def cerrar_error():
            error_window.destroy()
            # Limpiar el combobox en caso de error
            self.pedido_combobox['values'] = []
            self.pedido_combobox.set('')
            self.limpiar_campos()
        
        tk.Button(main_frame, text="Aceptar", 
                 command=cerrar_error,
                 bg='#f44336', fg='white', font=('Arial', 12)).pack()

    def limpiar_campos(self):
        # Limpiar datos del cliente
        self.cliente_label.config(text="")
        self.rfc_label.config(text="")
        self.regimen_label.config(text="")
        
        # Limpiar productos
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Limpiar totales
        self.subtotal = Decimal('0.00')
        self.iva = Decimal('0.00')
        self.total = Decimal('0.00')
        self.subtotal_label.config(text="$0.00")
        self.iva_label.config(text="$0.00")
        self.total_label.config(text="$0.00")
        
        # Limpiar pedido seleccionado
        self.pedido_seleccionado = None

    def on_pedido_selected(self, event):
        try:
            if not self.pedido_combobox.get():
                return
                
            pedido_id = self.pedido_combobox.get().split(" - ")[0]
            
            # Obtener detalles del pedido
            detalles = self.factura_manager.get_detalle_pedido(pedido_id)
            if not detalles:
                raise ValueError(f"No se encontraron detalles para el pedido {pedido_id}")
            
            # Obtener datos del cliente
            pedido = Pedido.from_db(self.db, pedido_id)
            if not pedido:
                raise ValueError(f"No se encontró el pedido {pedido_id}")
            
            cliente = Cliente.from_db(self.db, pedido.cliente_id)
            if not cliente:
                raise ValueError(f"No se encontró el cliente para el pedido {pedido_id}")
            
            # Actualizar datos del cliente
            self.cliente_label.config(text=f"Cliente: {cliente.nombre}")
            self.rfc_label.config(text=f"RFC: {cliente.rfc}")
            self.regimen_label.config(text=f"Régimen Fiscal: {cliente.regimen_fiscal}")
            
            # Limpiar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Insertar productos
            self.subtotal = Decimal('0.00')
            for detalle in detalles:
                cantidad = detalle[3]
                precio = Decimal(str(detalle[2]))
                subtotal = precio * cantidad
                self.subtotal += subtotal
                
                self.tree.insert("", tk.END, values=(
                    detalle[1],  # Nombre del producto
                    cantidad,
                    f"${precio:.2f}",
                    f"${subtotal:.2f}"
                ))
            
            # Calcular totales
            self.iva = self.subtotal * Decimal('0.16')
            self.total = self.subtotal + self.iva
            
            # Actualizar etiquetas
            self.subtotal_label.config(text=f"${self.subtotal:.2f}")
            self.iva_label.config(text=f"${self.iva:.2f}")
            self.total_label.config(text=f"${self.total:.2f}")
            
            # Guardar pedido seleccionado
            self.pedido_seleccionado = pedido_id
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el pedido: {str(e)}")
            self.limpiar_campos()

    def verificar_permisos_usuario(self):
        """Verifica si el usuario actual tiene permisos para generar facturas"""
        try:
            # Verificar si el usuario tiene rol de ADMINISTRADOR o CONTADOR
            if USUARIO_ACTUAL['rol'] in ['ADMINISTRADOR', 'CONTADOR']:
                return True
            
            # Si no tiene los roles necesarios, verificar permisos específicos
            query = """
                SELECT 1 FROM Permisos_Usuario 
                WHERE usuario_id = %s AND permiso = 'GENERAR_FACTURA'
            """
            resultado = self.db.fetch_one(query, (USUARIO_ACTUAL['id'],))
            return resultado is not None

        except Exception as e:
            logger.error(f"Error al verificar permisos: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def generar_factura(self):
        try:
            if not self.pedido_seleccionado:
                messagebox.showerror("Error", "Seleccione un pedido para generar la factura")
                return

            # Verificar permisos
            if not self.verificar_permisos_usuario():
                messagebox.showerror("Error", "No tiene permisos para generar facturas")
                return

            # Obtener datos del pedido y cliente
            pedido = Pedido.from_db(self.db, self.pedido_seleccionado)
            if not pedido:
                messagebox.showerror("Error", "No se pudo obtener los datos del pedido")
                return

            cliente = Cliente.from_db(self.db, pedido.cliente_id)
            if not cliente:
                messagebox.showerror("Error", "No se pudo obtener los datos del cliente")
                return

            # E1. Validar datos fiscales del cliente
            if not self.validar_datos_fiscales(cliente):
                return

            # Mostrar ventana de confirmación personalizada
            if not self.mostrar_confirmacion():
                return

            # E2. Intentar conexión con SAT (simulado)
            if not self.verificar_conexion_sat():
                return

            # Generar ID de factura
            fecha_actual = datetime.datetime.now().strftime('%Y%m%d')
            factura_id = f"F{fecha_actual}{self.pedido_seleccionado}"

            # Crear y mostrar la ventana de factura
            self.mostrar_factura(factura_id, pedido, cliente)

            # Actualizar estado del pedido a FACTURADO
            self.actualizar_estado_pedido(self.pedido_seleccionado)

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar factura: {str(e)}")
            logger.error(f"Error al generar factura: {str(e)}")
            logger.error(traceback.format_exc())

    def validar_datos_fiscales(self, cliente):
        """E1. Valida los datos fiscales del cliente"""
        try:
            # Validar RFC
            if not self.validar_rfc(cliente.rfc):
                self.mostrar_error_fiscal("RFC incorrecto", 
                    f"El RFC '{cliente.rfc}' no es válido.\n\nS1.1. Se debe solicitar actualización al administrador.\nS1.2. Caso de uso finaliza hasta que se haga la corrección.")
                return False

            # Validar dirección fiscal
            if not cliente.direccion_fiscal or len(cliente.direccion_fiscal.strip()) < 10:
                self.mostrar_error_fiscal("Dirección fiscal incompleta",
                    f"La dirección fiscal del cliente está incompleta.\n\nS1.1. Se debe solicitar actualización al administrador.\nS1.2. Caso de uso finaliza hasta que se haga la corrección.")
                return False

            # Validar régimen fiscal
            if not cliente.regimen_fiscal or cliente.regimen_fiscal.strip() == "":
                self.mostrar_error_fiscal("Régimen fiscal no especificado",
                    f"El régimen fiscal del cliente no está especificado.\n\nS1.1. Se debe solicitar actualización al administrador.\nS1.2. Caso de uso finaliza hasta que se haga la corrección.")
                return False

            return True

        except Exception as e:
            logger.error(f"Error al validar datos fiscales: {str(e)}")
            return False

    def validar_rfc(self, rfc):
        """Valida el formato del RFC"""
        if not rfc:
            return False
        
        # RFC debe tener 12 o 13 caracteres
        if len(rfc) not in [12, 13]:
            return False
        
        # RFC debe contener solo letras y números
        if not rfc.replace('-', '').isalnum():
            return False
        
        # Validaciones básicas adicionales
        # Para personas físicas: 4 letras + 6 números + 3 caracteres
        # Para personas morales: 3 letras + 6 números + 3 caracteres
        if len(rfc) == 13:  # Persona física
            if not (rfc[:4].isalpha() and rfc[4:10].isdigit() and rfc[10:].isalnum()):
                return False
        elif len(rfc) == 12:  # Persona moral
            if not (rfc[:3].isalpha() and rfc[3:9].isdigit() and rfc[9:].isalnum()):
                return False
        
        return True

    def mostrar_error_fiscal(self, titulo, mensaje):
        """Muestra error de datos fiscales y bloquea facturación"""
        # Crear ventana de error fiscal
        error_window = tk.Toplevel(self.root)
        error_window.title(f"Error de Datos Fiscales - {titulo}")
        error_window.geometry("500x300")
        error_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        error_window.attributes('-topmost', True)
        error_window.transient(self.root)
        error_window.grab_set()
        
        # Centrar la ventana
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (error_window.winfo_screenheight() // 2) - (300 // 2)
        error_window.geometry(f"500x300+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(error_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de error
        error_label = tk.Label(main_frame, text="🚫", font=('Arial', 24), bg='white')
        error_label.pack(pady=(0, 10))
        
        # Título
        titulo_label = tk.Label(main_frame, text=titulo, 
                               font=('Arial', 16, 'bold'), bg='white', fg='red')
        titulo_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text=mensaje,
                                font=('Arial', 11), 
                                bg='white',
                                justify=tk.LEFT,
                                wraplength=450)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        tk.Button(main_frame, text="Entendido", 
                 command=error_window.destroy,
                 bg='#f44336', fg='white', font=('Arial', 12)).pack()

    def verificar_conexion_sat(self):
        """E2. Verifica conexión con SAT con reintentos"""
        max_intentos = 2
        for intento in range(max_intentos + 1):
            try:
                # Simular verificación de conexión con SAT
                if self.simular_conexion_sat():
                    return True
                else:
                    if intento < max_intentos:
                        print(f"Intento {intento + 1} fallido. Reintentando...")
                        time.sleep(1)  # Esperar 1 segundo antes del reintento
                    else:
                        self.mostrar_error_sat()
                        return False
            except Exception as e:
                if intento < max_intentos:
                    print(f"Error en intento {intento + 1}: {e}. Reintentando...")
                    time.sleep(1)
                else:
                    self.mostrar_error_sat()
                    return False
        return False

    def simular_conexion_sat(self):
        """Simula la conexión con el SAT"""
        import random
        # Simular fallo ocasional (20% de probabilidad)
        return random.random() > 0.2

    def mostrar_error_sat(self):
        """E2.1. Muestra error de conexión SAT y notifica al administrador"""
        # Crear ventana de error SAT
        error_window = tk.Toplevel(self.root)
        error_window.title("Error de Conexión SAT")
        error_window.geometry("500x300")
        error_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        error_window.attributes('-topmost', True)
        error_window.transient(self.root)
        error_window.grab_set()
        
        # Centrar la ventana
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (error_window.winfo_screenheight() // 2) - (300 // 2)
        error_window.geometry(f"500x300+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(error_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de error
        error_label = tk.Label(main_frame, text="🌐", font=('Arial', 24), bg='white')
        error_label.pack(pady=(0, 10))
        
        # Título
        titulo_label = tk.Label(main_frame, text="Error de Conexión SAT", 
                               font=('Arial', 16, 'bold'), bg='white', fg='red')
        titulo_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text="E2. Error en conexión con el SAT.\n\nE2.1. El sistema reintentó 2 veces antes de notificar al administrador.\n\nSe ha notificado al administrador del sistema.\n\nPor favor, intente más tarde.",
                                font=('Arial', 11), 
                                bg='white',
                                justify=tk.LEFT,
                                wraplength=450)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        tk.Button(main_frame, text="Entendido", 
                 command=error_window.destroy,
                 bg='#f44336', fg='white', font=('Arial', 12)).pack()
        
        # Notificar al administrador (simulado)
        self.notificar_administrador_sat()

    def notificar_administrador_sat(self):
        """Notifica al administrador sobre el error de conexión SAT"""
        try:
            # Aquí se podría implementar:
            # - Envío de email al administrador
            # - Registro en log del sistema
            # - Notificación en dashboard
            print("NOTIFICACIÓN AL ADMINISTRADOR: Error de conexión SAT")
            logger.error("Error de conexión SAT - Notificado al administrador")
        except Exception as e:
            logger.error(f"Error al notificar al administrador: {str(e)}")

    def mostrar_confirmacion(self):
        """Muestra una ventana de confirmación personalizada que se mantiene arriba"""
        # Variable para almacenar el resultado
        resultado = [False]
        
        # Crear ventana de confirmación
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Confirmar Generación de Factura")
        confirm_window.geometry("400x250")
        confirm_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        confirm_window.attributes('-topmost', True)
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # Centrar la ventana
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (250 // 2)
        confirm_window.geometry(f"400x250+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(confirm_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de pregunta
        pregunta_label = tk.Label(main_frame, text="❓", font=('Arial', 24), bg='white')
        pregunta_label.pack(pady=(0, 10))
        
        # Título
        titulo_label = tk.Label(main_frame, text="Confirmar Generación", 
                               font=('Arial', 16, 'bold'), bg='white')
        titulo_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text="¿Desea generar la factura\npara este pedido?",
                                font=('Arial', 12), 
                                bg='white',
                                justify=tk.CENTER)
        mensaje_label.pack(pady=(0, 20))
        
        # Frame para botones
        botones_frame = tk.Frame(main_frame, bg='white')
        botones_frame.pack()
        
        def confirmar():
            resultado[0] = True
            confirm_window.destroy()
        
        def cancelar():
            resultado[0] = False
            confirm_window.destroy()
        
        # Botones
        tk.Button(botones_frame, text="Sí, Generar", 
                 command=confirmar,
                 bg='#4CAF50', fg='white', font=('Arial', 12),
                 width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(botones_frame, text="Cancelar", 
                 command=cancelar,
                 bg='#f44336', fg='white', font=('Arial', 12),
                 width=12).pack(side=tk.LEFT)
        
        # Esperar a que se cierre la ventana
        confirm_window.wait_window()
        
        return resultado[0]

    def actualizar_estado_pedido(self, pedido_id):
        """Marca el pedido como procesado sin cambiar su estado"""
        try:
            # En lugar de cambiar el estado, vamos a registrar que ya fue facturado
            # insertando un registro en la tabla Factura para evitar duplicados
            fecha_actual = datetime.datetime.now()
            
            # Insertar registro en Factura para marcar como facturado
            self.db.cursor.execute("""
                INSERT INTO Factura (id, pedido_id, fecha_emision, total)
                VALUES (%s, %s, %s, %s)
            """, (f"F{pedido_id}", pedido_id, fecha_actual, self.total))
            
            if self.db.cursor.rowcount > 0:
                self.db.connection.commit()
                print(f"Pedido {pedido_id} marcado como facturado")
                
                # Limpiar campos
                self.limpiar_campos()
                
            else:
                print(f"No se pudo marcar el pedido {pedido_id} como facturado")
                
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al marcar pedido como facturado: {str(e)}")
            messagebox.showerror("Error", f"Error al marcar pedido como facturado: {str(e)}")

    def mostrar_factura(self, factura_id, pedido, cliente):
        """Muestra la factura en una ventana separada"""
        # Crear ventana de factura
        factura_window = tk.Toplevel(self.root)
        factura_window.title(f"Factura {factura_id}")
        factura_window.geometry("600x750")
        factura_window.configure(bg='white')
        
        # Hacer la ventana modal y persistente
        factura_window.transient(self.root)
        factura_window.grab_set()
        factura_window.focus_set()
        
        # Centrar la ventana
        factura_window.update_idletasks()
        x = (factura_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (factura_window.winfo_screenheight() // 2) - (750 // 2)
        factura_window.geometry(f"600x750+{x}+{y}")

        # Frame principal
        main_frame = tk.Frame(factura_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Encabezado de la factura
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Título
        titulo_label = tk.Label(header_frame, text="FACTURA", 
                               font=('Arial', 20, 'bold'), bg='white')
        titulo_label.pack()

        # Información de la factura
        factura_info_frame = tk.Frame(header_frame, bg='white')
        factura_info_frame.pack(fill=tk.X, pady=10)

        tk.Label(factura_info_frame, text=f"Factura No.: {factura_id}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)
        tk.Label(factura_info_frame, text=f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)
        tk.Label(factura_info_frame, text=f"Pedido: {pedido.id}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)

        # Información del cliente
        cliente_frame = tk.Frame(main_frame, bg='white')
        cliente_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(cliente_frame, text="DATOS DEL CLIENTE", 
                font=('Arial', 14, 'bold'), bg='white').pack(anchor=tk.W)
        tk.Label(cliente_frame, text=f"Nombre: {cliente.nombre}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)
        tk.Label(cliente_frame, text=f"RFC: {cliente.rfc}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)
        tk.Label(cliente_frame, text=f"Régimen Fiscal: {cliente.regimen_fiscal}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)
        tk.Label(cliente_frame, text=f"Dirección: {cliente.direccion_fiscal}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.W)

        # Campo para correo electrónico de envío
        email_frame = tk.Frame(main_frame, bg='white')
        email_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(email_frame, text="Correo para envío de factura:", font=('Arial', 12), bg='white').pack(side=tk.LEFT, padx=(0, 10))
        email_entry = tk.Entry(email_frame, font=('Arial', 12), width=35)
        email_entry.pack(side=tk.LEFT)

        # Productos
        productos_frame = tk.Frame(main_frame, bg='white')
        productos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        tk.Label(productos_frame, text="PRODUCTOS", 
                font=('Arial', 14, 'bold'), bg='white').pack(anchor=tk.W)

        # Treeview para productos
        tree = ttk.Treeview(productos_frame, 
                           columns=("cantidad", "precio", "subtotal"), 
                           show="headings", height=8)
        tree.heading("cantidad", text="Cantidad")
        tree.heading("precio", text="Precio Unitario")
        tree.heading("subtotal", text="Subtotal")
        tree.column("cantidad", width=100, anchor=tk.CENTER)
        tree.column("precio", width=150, anchor=tk.E)
        tree.column("subtotal", width=150, anchor=tk.E)
        tree.pack(fill=tk.BOTH, expand=True)

        # Insertar productos
        for producto, cantidad in pedido.productos:
            precio = producto.precio
            subtotal = precio * cantidad
            tree.insert("", tk.END, values=(
                cantidad,
                f"${precio:.2f}",
                f"${subtotal:.2f}"
            ))

        # Totales
        totales_frame = tk.Frame(main_frame, bg='white')
        totales_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(totales_frame, text="TOTALES", 
                font=('Arial', 14, 'bold'), bg='white').pack(anchor=tk.E)

        tk.Label(totales_frame, text=f"Subtotal: ${self.subtotal:.2f}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.E)
        tk.Label(totales_frame, text=f"IVA (16%): ${self.iva:.2f}", 
                font=('Arial', 12), bg='white').pack(anchor=tk.E)
        tk.Label(totales_frame, text=f"Total: ${self.total:.2f}", 
                font=('Arial', 14, 'bold'), bg='white').pack(anchor=tk.E)

        # Botones
        botones_frame = tk.Frame(main_frame, bg='white')
        botones_frame.pack(fill=tk.X, pady=(20, 0))

        def cerrar_factura():
            factura_window.destroy()
            # Recargar pedidos pendientes después de cerrar la ventana
            self.cargar_pedidos_pendientes()

        def enviar_por_email():
            correo_destino = email_entry.get().strip()
            if not correo_destino:
                self.mostrar_error_email("Por favor ingrese un correo para el envío de la factura.")
                return
            if not self.validar_email(correo_destino):
                self.mostrar_error_email("El correo ingresado no es válido.")
                return
            # Crear el contenido del email
            asunto = f"Factura {factura_id} - {EMAIL_CONFIG['nombre_empresa']}"
            cuerpo = f"Estimado cliente,\n\nAdjunto encontrará la factura {factura_id} correspondiente a su pedido {pedido.id}.\n\nDatos del cliente:\nNombre: {cliente.nombre}\nRFC: {cliente.rfc}\nRégimen Fiscal: {cliente.regimen_fiscal}\nDirección: {cliente.direccion_fiscal}\n\nPor favor, adjunte manualmente el archivo de la factura generado por el sistema.\n\nSaludos cordiales."
            # Codificar para URL
            mailto_url = f"mailto:{correo_destino}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
            webbrowser.open(mailto_url)
            # Mostrar mensaje para adjuntar manualmente
            self.mostrar_confirmacion_email(correo_destino, factura_id, adjuntar=True)

        def imprimir_factura():
            messagebox.showinfo("Impresión", "La factura se enviará a la impresora predeterminada")

        # Botón principal para enviar (siempre visible y primero)
        enviar_btn = tk.Button(botones_frame, text="Enviar", 
                 command=enviar_por_email,
                 bg='#2196F3', fg='white', font=('Arial', 14, 'bold'), width=12)
        enviar_btn.pack(side=tk.LEFT, padx=(0, 20))

        imprimir_btn = tk.Button(botones_frame, text="Imprimir", 
                 command=imprimir_factura,
                 bg='#4CAF50', fg='white', font=('Arial', 12))
        imprimir_btn.pack(side=tk.LEFT, padx=(0, 10))

        cerrar_btn = tk.Button(botones_frame, text="Cerrar", 
                 command=cerrar_factura,
                 bg='#f44336', fg='white', font=('Arial', 12))
        cerrar_btn.pack(side=tk.LEFT)

    def mostrar_confirmacion_email(self, email_cliente, factura_id, adjuntar=False):
        """Muestra confirmación de envío de email o recordatorio de adjuntar"""
        # Crear ventana de confirmación
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Email Enviar")
        confirm_window.geometry("400x220")
        confirm_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        confirm_window.attributes('-topmost', True)
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # Centrar la ventana
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (220 // 2)
        confirm_window.geometry(f"400x220+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(confirm_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de éxito
        success_label = tk.Label(main_frame, text="✅", font=('Arial', 24), bg='white')
        success_label.pack(pady=(0, 10))
        
        # Mensaje
        if adjuntar:
            mensaje = f"Se abrió el cliente de correo para enviar la factura {factura_id} a {email_cliente}.\n\nPor favor, adjunte manualmente el archivo de la factura antes de enviar el correo."
        else:
            mensaje = f"Factura {factura_id} enviada exitosamente a {email_cliente}"
        mensaje_label = tk.Label(main_frame, 
                                text=mensaje,
                                font=('Arial', 12), 
                                bg='white',
                                justify=tk.CENTER,
                                wraplength=350)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        tk.Button(main_frame, text="Aceptar", 
                 command=confirm_window.destroy,
                 bg='#4CAF50', fg='white', font=('Arial', 12)).pack()

    def mostrar_error_email(self, mensaje):
        """Muestra error de envío de email"""
        # Crear ventana de error
        error_window = tk.Toplevel(self.root)
        error_window.title("Error al Enviar Email")
        error_window.geometry("400x200")
        error_window.configure(bg='white')
        
        # Hacer que se mantenga arriba
        error_window.attributes('-topmost', True)
        error_window.transient(self.root)
        error_window.grab_set()
        
        # Centrar la ventana
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (error_window.winfo_screenheight() // 2) - (200 // 2)
        error_window.geometry(f"400x200+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(error_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icono de error
        error_label = tk.Label(main_frame, text="❌", font=('Arial', 24), bg='white')
        error_label.pack(pady=(0, 10))
        
        # Mensaje
        mensaje_label = tk.Label(main_frame, 
                                text=mensaje,
                                font=('Arial', 12), 
                                bg='white',
                                justify=tk.CENTER,
                                wraplength=350)
        mensaje_label.pack(pady=(0, 20))
        
        # Botón cerrar
        tk.Button(main_frame, text="Aceptar", 
                 command=error_window.destroy,
                 bg='#f44336', fg='white', font=('Arial', 12)).pack()

    def on_closing(self):
        # Quitar el atributo topmost antes de cerrar
        self.root.attributes('-topmost', False)
        if self.db:
            self.db.close()
        self.root.destroy()

    def validar_email(self, email):
        """Valida el formato básico de un correo electrónico"""
        import re
        patron = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        return re.match(patron, email) is not None

def ejecutar():
    try:
        root = tk.Tk()
        app = GenerarFacturaGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", 
                           f"Error al iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    ejecutar() 
import sqlite3
from datetime import datetime

def crear_base_datos():
    conn = sqlite3.connect('Base_datos.db')
    cursor = conn.cursor()

    # PRIMERO: Crear tablas sin dependencias
    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    -- Tabla Cliente
    CREATE TABLE IF NOT EXISTS Cliente (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        direccion TEXT
    );

    -- Tabla Producto
    CREATE TABLE IF NOT EXISTS Producto (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        stock INTEGER NOT NULL,
        estado TEXT CHECK (estado IN ('ACTIVO', 'DESCONTINUADO', 'EN_PROMOCION', 'AGOTADO'))
    );

    -- Tabla Vendedor (versión simplificada)
    CREATE TABLE IF NOT EXISTS Vendedor (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );

    -- Tabla Tienda (versión simplificada)
    CREATE TABLE IF NOT EXISTS Tienda (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );

    -- Tabla Proveedor
    CREATE TABLE IF NOT EXISTS Proveedor (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );
    """)

    # SEGUNDO: Tablas con dependencias simples
    cursor.executescript("""
    -- Tabla Pedido
    CREATE TABLE IF NOT EXISTS Pedido (
        id TEXT PRIMARY KEY,
        cliente_id TEXT REFERENCES Cliente(id),
        fecha TEXT NOT NULL,
        estado TEXT CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'EN_RUTA', 'ENTREGADO', 'CANCELADO'))
    );

    -- Tabla Factura
    CREATE TABLE IF NOT EXISTS Factura (
        id TEXT PRIMARY KEY,
        pedido_id TEXT,
        fecha_emision TEXT NOT NULL,
        total REAL NOT NULL,
        cliente TEXT NOT NULL,
        estado TEXT DEFAULT 'PENDIENTE',
        fecha_pago TEXT
    );

    -- Tabla RutaEntrega
    CREATE TABLE IF NOT EXISTS RutaEntrega (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id TEXT REFERENCES Vendedor(id)
    );
    """)

    # TERCERO: Tablas con múltiples dependencias
    cursor.executescript("""
    -- Tabla Pedido_Producto
    CREATE TABLE IF NOT EXISTS Pedido_Producto (
        pedido_id TEXT REFERENCES Pedido(id) ON DELETE CASCADE,
        producto_id TEXT REFERENCES Producto(id),
        cantidad INTEGER NOT NULL,
        PRIMARY KEY (pedido_id, producto_id)
    );

    -- Tabla Transaccion
    CREATE TABLE IF NOT EXISTS Transaccion (
        id TEXT PRIMARY KEY,
        monto REAL NOT NULL,
        metodo_pago TEXT NOT NULL,
        factura_id TEXT NOT NULL REFERENCES Factura(id),
        fecha TEXT NOT NULL,
        estado TEXT NOT NULL,
        timestamp_inicio REAL,
        timestamp_fin REAL
    );

    -- Índice para Factura
    CREATE UNIQUE INDEX IF NOT EXISTS idx_factura_pedido ON Factura(pedido_id);
    """)

    # CUARTO: Tablas con relaciones complejas
    cursor.executescript("""
    -- Tabla Negociacion
    CREATE TABLE IF NOT EXISTS Negociacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id TEXT REFERENCES Vendedor(id),
        tienda_id TEXT REFERENCES Tienda(id),
        terminos TEXT
    );

    -- Tabla RutaEntrega_Pedido
    CREATE TABLE IF NOT EXISTS RutaEntrega_Pedido (
        ruta_id INTEGER REFERENCES RutaEntrega(id),
        pedido_id TEXT REFERENCES Pedido(id),
        PRIMARY KEY (ruta_id, pedido_id)
    );

    -- Tabla Inventario
    CREATE TABLE IF NOT EXISTS Inventario (
        producto_id TEXT REFERENCES Producto(id),
        sucursal_id TEXT,
        cantidad INTEGER NOT NULL,
        PRIMARY KEY (producto_id, sucursal_id)
    );

    -- Tabla Administrador
    CREATE TABLE IF NOT EXISTS Administrador (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    );

    -- Tabla Precio_Proveedor_Producto
    CREATE TABLE IF NOT EXISTS Precio_Proveedor_Producto (
        proveedor_id TEXT REFERENCES Proveedor(id),
        producto_id TEXT REFERENCES Producto(id),
        precio REAL,
        PRIMARY KEY (proveedor_id, producto_id)
    );

    -- Tabla OrdenCompra
    CREATE TABLE IF NOT EXISTS OrdenCompra (
        id TEXT PRIMARY KEY,
        proveedor_id TEXT REFERENCES Proveedor(id),
        estado TEXT
    );

    -- Tabla HistorialCambios
    CREATE TABLE IF NOT EXISTS HistorialCambios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id TEXT REFERENCES Producto(id),
        proveedor_id TEXT REFERENCES Proveedor(id),
        fecha TEXT NOT NULL,
        nuevo_precio REAL,
        nuevo_stock INTEGER
    );
    """)

    # DATOS INICIALES DE PRUEBA (versión simplificada)
    fecha_actual = datetime.now().strftime('%Y-%m-%d')

    # Insertar tiendas (solo con id y nombre)
    cursor.executemany(
        "INSERT OR IGNORE INTO Tienda (id, nombre) VALUES (?, ?)",
        [
            ('TND-001', 'Tienda Central'),
            ('TND-002', 'Tienda Norte'),
            ('TND-003', 'Tienda Sur')
        ]
    )

    # Insertar vendedores (solo con id y nombre)
    cursor.executemany(
        "INSERT OR IGNORE INTO Vendedor (id, nombre) VALUES (?, ?)",
        [
            ('VND-001', 'Carlos Mendoza'),
            ('VND-002', 'Ana López'),
            ('VND-003', 'Pedro Ramírez')
        ]
    )

    # Insertar clientes
    cursor.executemany(
        "INSERT OR IGNORE INTO Cliente (id, nombre, direccion) VALUES (?, ?, ?)",
        [
            ('CLI-001', 'Juan Pérez', 'Calle Falsa 123'),
            ('CLI-002', 'María García', 'Av. Siempre Viva 456'),
            ('CLI-003', 'Roberto Sánchez', 'Boulevard Los Olivos 789')
        ]
    )
    
    # Insertar productos
    cursor.executemany(
        "INSERT OR IGNORE INTO Producto (id, nombre, precio, stock, estado) VALUES (?, ?, ?, ?, ?)",
        [
            ('PROD-001', 'Laptop Gamer', 15000.50, 10, 'ACTIVO'),
            ('PROD-002', 'Monitor 24"', 3500.00, 15, 'ACTIVO'),
            ('PROD-003', 'Teclado Mecánico', 1200.00, 20, 'ACTIVO'),
            ('PROD-004', 'Mouse Inalámbrico', 600.00, 30, 'ACTIVO'),
            ('PROD-005', 'Impresora Multifuncional', 4200.00, 5, 'ACTIVO')
        ]
    )

    conn.commit()
    conn.close()
    print("✅ Base de datos creada exitosamente con todas las tablas y datos iniciales")

if __name__ == "__main__":
    crear_base_datos()
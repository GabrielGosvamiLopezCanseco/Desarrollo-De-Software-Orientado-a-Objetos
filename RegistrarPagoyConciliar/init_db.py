import sqlite3
from datetime import datetime

def crear_base_datos():
    conn = sqlite3.connect('Base_datos.db')
    cursor = conn.cursor()

    # PRIMERO: Crear tablas sin dependencias
    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    -- Tabla Cliente (sin dependencias)
    CREATE TABLE IF NOT EXISTS Cliente (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        direccion TEXT
    );

    -- Tabla Producto (sin dependencias)
    CREATE TABLE IF NOT EXISTS Producto (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        stock INTEGER NOT NULL,
        estado TEXT CHECK (estado IN ('ACTIVO', 'DESCONTINUADO', 'EN_PROMOCION', 'AGOTADO'))
    );

    -- Tabla Vendedor (sin dependencias)
    CREATE TABLE IF NOT EXISTS Vendedor (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );

    -- Tabla Tienda (sin dependencias)
    CREATE TABLE IF NOT EXISTS Tienda (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );

    -- Tabla Proveedor (sin dependencias)
    CREATE TABLE IF NOT EXISTS Proveedor (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL
    );
    """)

    # SEGUNDO: Tablas con dependencias simples
    cursor.executescript("""
    -- Tabla Pedido (depende de Cliente)
    CREATE TABLE IF NOT EXISTS Pedido (
        id TEXT PRIMARY KEY,
        cliente_id TEXT REFERENCES Cliente(id),
        fecha TEXT NOT NULL,
        estado TEXT CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'EN_RUTA', 'ENTREGADO', 'CANCELADO'))
    );

    -- Tabla Factura (depende de Pedido) - SIN la referencia UNIQUE temporalmente
    CREATE TABLE IF NOT EXISTS Factura (
        id TEXT PRIMARY KEY,
        pedido_id TEXT,
        fecha_emision TEXT NOT NULL,
        total REAL NOT NULL,
        cliente TEXT NOT NULL,
        estado TEXT DEFAULT 'PENDIENTE',
        fecha_pago TEXT
    );

    -- Tabla RutaEntrega (depende de Vendedor)
    CREATE TABLE IF NOT EXISTS RutaEntrega (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id TEXT REFERENCES Vendedor(id)
    );
    """)

    # TERCERO: Tablas con múltiples dependencias
    cursor.executescript("""
    -- Tabla Pedido_Producto (depende de Pedido y Producto)
    CREATE TABLE IF NOT EXISTS Pedido_Producto (
        pedido_id TEXT REFERENCES Pedido(id) ON DELETE CASCADE,
        producto_id TEXT REFERENCES Producto(id),
        cantidad INTEGER NOT NULL,
        PRIMARY KEY (pedido_id, producto_id)
    );

    -- Tabla Transaccion (depende de Factura)
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

    -- Ahora que Factura existe, agregamos la restricción UNIQUE
    CREATE UNIQUE INDEX IF NOT EXISTS idx_factura_pedido ON Factura(pedido_id);
    """)

    # CUARTO: Tablas con relaciones complejas
    cursor.executescript("""
    -- Tabla Negociacion (depende de Vendedor y Tienda)
    CREATE TABLE IF NOT EXISTS Negociacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id TEXT REFERENCES Vendedor(id),
        tienda_id TEXT REFERENCES Tienda(id),
        terminos TEXT
    );

    -- Tabla RutaEntrega_Pedido (depende de RutaEntrega y Pedido)
    CREATE TABLE IF NOT EXISTS RutaEntrega_Pedido (
        ruta_id INTEGER REFERENCES RutaEntrega(id),
        pedido_id TEXT REFERENCES Pedido(id),
        PRIMARY KEY (ruta_id, pedido_id)
    );

    -- Tabla Inventario (depende de Producto)
    CREATE TABLE IF NOT EXISTS Inventario (
        producto_id TEXT REFERENCES Producto(id),
        sucursal_id TEXT,
        cantidad INTEGER NOT NULL,
        PRIMARY KEY (producto_id, sucursal_id)
    );

    -- Tabla Administrador (sin dependencias)
    CREATE TABLE IF NOT EXISTS Administrador (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    );

    -- Tabla Precio_Proveedor_Producto (depende de Proveedor y Producto)
    CREATE TABLE IF NOT EXISTS Precio_Proveedor_Producto (
        proveedor_id TEXT REFERENCES Proveedor(id),
        producto_id TEXT REFERENCES Producto(id),
        precio REAL,
        PRIMARY KEY (proveedor_id, producto_id)
    );

    -- Tabla OrdenCompra (depende de Proveedor)
    CREATE TABLE IF NOT EXISTS OrdenCompra (
        id TEXT PRIMARY KEY,
        proveedor_id TEXT REFERENCES Proveedor(id),
        estado TEXT
    );

    -- Tabla HistorialCambios (depende de Producto y Proveedor)
    CREATE TABLE IF NOT EXISTS HistorialCambios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id TEXT REFERENCES Producto(id),
        proveedor_id TEXT REFERENCES Proveedor(id),
        fecha TEXT NOT NULL,
        nuevo_precio REAL,
        nuevo_stock INTEGER
    );
    """)

    # Datos iniciales de prueba
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    cursor.executemany(
        "INSERT OR IGNORE INTO Cliente (id, nombre) VALUES (?, ?)",
        [('CLI-001', 'Juan Pérez'), ('CLI-002', 'María García')]
    )
    
    cursor.execute(
        "INSERT OR IGNORE INTO Producto (id, nombre, precio, stock, estado) VALUES (?, ?, ?, ?, ?)",
        ('PROD-001', 'Laptop Gamer', 15000.50, 10, 'ACTIVO')
    )

    conn.commit()
    conn.close()
    print("✅ Base de datos creada exitosamente con todas las tablas")

if __name__ == "__main__":
    crear_base_datos()
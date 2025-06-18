-- ============================================
-- BASE DE DATOS: Sistema de Pedidos y Facturación
-- Compatible con PostgreSQL
-- Con soporte para CFDI 4.0 y gestión de proveedores
-- ============================================

-- Tabla: Cliente
CREATE TABLE Cliente (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    direccion TEXT,
    rfc VARCHAR(13),
    regimen_fiscal VARCHAR(100),
    direccion_fiscal TEXT
);

-- Tabla: Producto
CREATE TABLE Producto (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    stock INTEGER NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('ACTIVO', 'DESCONTINUADO', 'EN_PROMOCION', 'AGOTADO'))
);

-- Tabla: Pedido
CREATE TABLE Pedido (
    id VARCHAR PRIMARY KEY,
    cliente_id VARCHAR REFERENCES Cliente(id),
    fecha DATE NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'EN_RUTA', 'ENTREGADO', 'CANCELADO'))
);

-- Tabla intermedia: Pedido_Producto
CREATE TABLE Pedido_Producto (
    pedido_id VARCHAR REFERENCES Pedido(id) ON DELETE CASCADE,
    producto_id VARCHAR REFERENCES Producto(id),
    cantidad INTEGER NOT NULL,
    PRIMARY KEY (pedido_id, producto_id)
);

-- Tabla: Factura
CREATE TABLE Factura (
    id VARCHAR PRIMARY KEY,
    pedido_id VARCHAR REFERENCES Pedido(id) UNIQUE,
    fecha_emision DATE NOT NULL,
    subtotal NUMERIC(10, 2),
    iva NUMERIC(10, 2),
    total NUMERIC(10, 2) NOT NULL,
    estatus VARCHAR(20) CHECK (estatus IN ('PENDIENTE', 'EMITIDA', 'CANCELADA')) DEFAULT 'PENDIENTE'
);

-- Tabla: CuentaPorCobrar
CREATE TABLE CuentaPorCobrar (
    id SERIAL PRIMARY KEY,
    factura_id VARCHAR REFERENCES Factura(id),
    cliente_id VARCHAR REFERENCES Cliente(id),
    fecha_emision DATE NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    estatus VARCHAR(20) CHECK (estatus IN ('PENDIENTE', 'PAGADA', 'VENCIDA')) DEFAULT 'PENDIENTE'
);

-- Tabla: Vendedor
CREATE TABLE Vendedor (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL
);

-- Tabla: Tienda
CREATE TABLE Tienda (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL
);

-- Tabla: Negociacion
CREATE TABLE Negociacion (
    id SERIAL PRIMARY KEY,
    vendedor_id VARCHAR REFERENCES Vendedor(id),
    tienda_id VARCHAR REFERENCES Tienda(id),
    terminos JSON
);

-- Tabla: RutaEntrega
CREATE TABLE RutaEntrega (
    id SERIAL PRIMARY KEY,
    vendedor_id VARCHAR REFERENCES Vendedor(id)
);

-- Tabla: RutaEntrega_Pedido
CREATE TABLE RutaEntrega_Pedido (
    ruta_id INTEGER REFERENCES RutaEntrega(id),
    pedido_id VARCHAR REFERENCES Pedido(id),
    PRIMARY KEY (ruta_id, pedido_id)
);

-- Tabla: Inventario
CREATE TABLE Inventario (
    producto_id VARCHAR REFERENCES Producto(id),
    sucursal_id VARCHAR,
    cantidad INTEGER NOT NULL,
    PRIMARY KEY (producto_id, sucursal_id)
);

-- Tabla: Administrador
CREATE TABLE Administrador (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL
);

-- Tabla: Proveedor
CREATE TABLE Proveedor (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL
);

-- Tabla: Precio_Proveedor_Producto
CREATE TABLE Precio_Proveedor_Producto (
    proveedor_id VARCHAR REFERENCES Proveedor(id),
    producto_id VARCHAR REFERENCES Producto(id),
    precio NUMERIC(10, 2),
    PRIMARY KEY (proveedor_id, producto_id)
);

-- Tabla: OrdenCompra
CREATE TABLE OrdenCompra (
    id VARCHAR PRIMARY KEY,
    proveedor_id VARCHAR REFERENCES Proveedor(id),
    estado VARCHAR(20)
);

-- Tabla: HistorialCambios
CREATE TABLE HistorialCambios (
    id SERIAL PRIMARY KEY,
    producto_id VARCHAR REFERENCES Producto(id),
    proveedor_id VARCHAR REFERENCES Proveedor(id),
    fecha TIMESTAMP NOT NULL,
    nuevo_precio NUMERIC(10,2),
    nuevo_stock INTEGER,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_modifico VARCHAR
);

-- Tabla: Notificacion
CREATE TABLE Notificacion (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50),
    mensaje TEXT,
    destinatario VARCHAR,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE
);

-- Tabla: LogErrorFactura
CREATE TABLE LogErrorFactura (
    id SERIAL PRIMARY KEY,
    factura_id VARCHAR REFERENCES Factura(id),
    codigo_error VARCHAR,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reintentos INTEGER DEFAULT 0
);

-- Tabla: Usuario (gestión de roles)
CREATE TABLE Usuario (
    id VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    rol VARCHAR(20) CHECK (rol IN ('ADMINISTRADOR', 'CONTADOR', 'PROVEEDOR', 'VENDEDOR'))
);

-- Tabla: Impuesto
CREATE TABLE Impuesto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    tasa NUMERIC(5,4) NOT NULL
);

-- Tabla: Sistema (registro de parámetros generales)
CREATE TABLE Sistema (
    clave VARCHAR PRIMARY KEY,
    valor TEXT NOT NULL
);

-- Tabla: Contador (usuario con rol específico extendido)
CREATE TABLE Contador (
    id VARCHAR PRIMARY KEY REFERENCES Usuario(id)
);

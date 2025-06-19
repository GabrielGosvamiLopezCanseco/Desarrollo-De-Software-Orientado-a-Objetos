-- Actualización de la base de datos para el caso de uso de Facturación

-- Insertar clientes con datos fiscales
INSERT INTO Cliente (id, nombre, direccion, rfc, regimen_fiscal, email) VALUES
('CLI001', 'Empresa ABC S.A. de C.V.', 'Av. Reforma 123, CDMX', 'ABC123456789', 'Persona Moral', 'contacto@empresaabc.com'),
('CLI002', 'Juan Pérez Morales', 'Calle Juárez 456, GDL', 'PEMJ800101ABC', 'Persona Física', 'juan.perez@email.com'),
('CLI003', 'Distribuidora XYZ', 'Blvd. Manuel Ávila Camacho 789, MTY', 'XYZ987654321', 'Persona Moral', 'ventas@xyz.com');

-- Insertar productos
INSERT INTO Producto (id, nombre, precio, stock, estado) VALUES
('PROD001', 'Laptop HP', 15000.00, 10, 'ACTIVO'),
('PROD002', 'Monitor Dell 24"', 3500.00, 15, 'ACTIVO'),
('PROD003', 'Teclado Mecánico', 1200.00, 20, 'ACTIVO'),
('PROD004', 'Mouse Gaming', 800.00, 25, 'ACTIVO'),
('PROD005', 'Audífonos Bluetooth', 1500.00, 30, 'ACTIVO');

-- Insertar pedidos
INSERT INTO Pedido (id, cliente_id, fecha, estado) VALUES
('PED001', 'CLI001', CURRENT_DATE - INTERVAL '2 days', 'ENTREGADO'),
('PED002', 'CLI002', CURRENT_DATE - INTERVAL '1 day', 'ENTREGADO'),
('PED003', 'CLI003', CURRENT_DATE, 'ENTREGADO');

-- Insertar productos en pedidos
INSERT INTO Pedido_Producto (pedido_id, producto_id, cantidad) VALUES
('PED001', 'PROD001', 2),
('PED001', 'PROD002', 2),
('PED001', 'PROD003', 2),
('PED002', 'PROD004', 5),
('PED002', 'PROD005', 5),
('PED003', 'PROD001', 1),
('PED003', 'PROD002', 1);

-- Insertar administrador
INSERT INTO Administrador (id, nombre, email) VALUES
('ADM001', 'Admin Principal', 'admin@sistema.com');

-- Insertar vendedor
INSERT INTO Vendedor (id, nombre) VALUES
('VEN001', 'Carlos Rodríguez');

-- Insertar tienda
INSERT INTO Tienda (id, nombre) VALUES
('TIE001', 'Tienda Central');

-- Insertar negociación
INSERT INTO Negociacion (vendedor_id, tienda_id, terminos) VALUES
('VEN001', 'TIE001', '{"descuento": 10, "plazo": 30}');

-- Insertar ruta de entrega
INSERT INTO RutaEntrega (vendedor_id) VALUES
('VEN001');

-- Asociar pedidos a ruta
INSERT INTO RutaEntrega_Pedido (ruta_id, pedido_id) VALUES
(1, 'PED001'),
(1, 'PED002'),
(1, 'PED003');

-- Insertar en inventario
INSERT INTO Inventario (producto_id, sucursal_id, cantidad) VALUES
('PROD001', 'TIE001', 10),
('PROD002', 'TIE001', 15),
('PROD003', 'TIE001', 20),
('PROD004', 'TIE001', 25),
('PROD005', 'TIE001', 30);

-- Insertar proveedor
INSERT INTO Proveedor (id, nombre) VALUES
('PROV001', 'TechDistribuidor');

-- Insertar precios de proveedor
INSERT INTO Precio_Proveedor_Producto (proveedor_id, producto_id, precio) VALUES
('PROV001', 'PROD001', 12000.00),
('PROV001', 'PROD002', 2800.00),
('PROV001', 'PROD003', 900.00),
('PROV001', 'PROD004', 600.00),
('PROV001', 'PROD005', 1200.00);

-- Insertar orden de compra
INSERT INTO OrdenCompra (id, proveedor_id, estado) VALUES
('OC001', 'PROV001', 'COMPLETADA');

-- Crear secuencia para IDs de factura si no existe
CREATE SEQUENCE IF NOT EXISTS factura_seq;

-- Crear función para generar IDs de factura
CREATE OR REPLACE FUNCTION generar_id_factura()
RETURNS VARCHAR AS $$
BEGIN
    RETURN 'FAC' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD(NEXTVAL('factura_seq')::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql; 
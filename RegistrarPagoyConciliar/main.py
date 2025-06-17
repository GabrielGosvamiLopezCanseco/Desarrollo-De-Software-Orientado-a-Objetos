from modelo import Factura
from persistencia import guardar_factura

# Crear y guardar factura
factura = Factura("FAC-001", "PED-001", 1500.50)
guardar_factura(factura)

# Ejemplo de pago
factura.marcar_como_pagada()
guardar_factura(factura)

print("Operación completada exitosamente")
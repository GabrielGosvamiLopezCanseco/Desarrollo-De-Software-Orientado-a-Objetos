import psycopg2

def conectar():
    return psycopg2.connect(
        dbname="tienda_base_datos",
        user="tu_usuario",
        password="nontraseña",
        host="localhost",
        port="5432"
    )

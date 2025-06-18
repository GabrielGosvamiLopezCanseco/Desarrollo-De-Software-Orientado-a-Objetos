# conexion.py
import sqlite3
from sqlite3 import Connection

def conectar() -> Connection:
    conn = sqlite3.connect("Base_datos.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")  # Mejor manejo de concurrencia
    return conn

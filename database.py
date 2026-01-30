import sqlite3
import os
from datetime import datetime

DB_FILE = 'estudios.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Tabla de estudios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estudios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_paciente TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            recibo TEXT UNIQUE NOT NULL,
            institucion TEXT DEFAULT 'REMadom',
            cliente TEXT,
            fecha TEXT,
            importe TEXT DEFAULT '0',
            metodo_pago TEXT,
            procesado INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de configuración (contador global)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)
    
    # Inicializar contador
    cur.execute("""
        INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('proximo_recibo', '1')
    """)
    
    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite inicializada")

init_db()

def obtener_proximo_recibo():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
    row = cur.fetchone()
    proximo = int(row[0])
    cur.execute("UPDATE configuracion SET valor = ? WHERE clave = 'proximo_recibo'", (str(proximo + 1),))
    conn.commit()
    conn.close()
    return proximo

def crear_estudio(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    recibo_numero = obtener_proximo_recibo()
    
    cur.execute("""
        INSERT INTO estudios (
            nombre_paciente, descripcion, recibo, institucion, 
            cliente, fecha, importe, metodo_pago, procesado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['nombre_paciente'],
        data['descripcion'],
        str(recibo_numero),
        data.get('institucion', 'REMadom'),
        data.get('cliente', ''),
        data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        str(data.get('importe', 0)),
        data.get('metodo_pago', ''),
        0
    ))
    
    estudio_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'id': estudio_id,
        'nombre_paciente': data['nombre_paciente'],
        'descripcion': data['descripcion'],
        'recibo': str(recibo_numero),
        'institucion': data.get('institucion', 'REMadom'),
        'cliente': data.get('cliente', ''),
        'fecha': data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        'importe': str(data.get('importe', 0)),
        'metodo_pago': data.get('metodo_pago', ''),
        'procesado': False
    }

def obtener_estudios_pendientes():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM estudios WHERE procesado = 0 ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    
    estudios = []
    for row in rows:
        estudios.append({
            'id': row[0],
            'nombre_paciente': row[1],
            'descripcion': row[2],
            'recibo': row[3],
            'institucion': row[4],
            'cliente': row[5],
            'fecha': row[6],
            'importe': row[7],
            'metodo_pago': row[8],
            'procesado': row[9] == 1
        })
    
    return estudios

def marcar_procesado(estudio_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE estudios SET procesado = 1 WHERE id = ?", (estudio_id,))
    conn.commit()
    conn.close()
    return True

def health_check():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM estudios")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM estudios WHERE procesado = 0")
    pendientes = cur.fetchone()[0]
    conn.close()
    
    return {
        'status': 'ok',
        'estudios_totales': total,
        'pendientes': pendientes,
        'message': 'Servidor DICOX activo (SQLite)'
    }



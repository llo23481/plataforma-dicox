import sqlite3
import os
from datetime import datetime

# Ruta persistente en Render
DB_PATH = '/opt/render/project/src/data/estudios.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
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
        INSERT OR IGNORE INTO configuracion (clave, valor) 
        VALUES ('proximo_recibo', '1')
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite inicializado: {DB_PATH}")

init_db()

def obtener_proximo_recibo():
    """Obtiene el próximo recibo"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
    valor = int(cur.fetchone()[0])
    conn.close()
    return valor

def actualizar_proximo_recibo(nuevo_valor):
    """Actualiza el contador"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE configuracion SET valor = ? WHERE clave = 'proximo_recibo'", (str(nuevo_valor),))
    conn.commit()
    conn.close()

def crear_estudio(data):
    """Crea un estudio"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    recibo = obtener_proximo_recibo()
    
    cur.execute("""
        INSERT INTO estudios (
            nombre_paciente, descripcion, recibo, institucion,
            cliente, fecha, importe, metodo_pago, procesado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['nombre_paciente'],
        data['descripcion'],
        str(recibo),
        data.get('institucion', 'REMadom'),
        data.get('cliente', ''),
        data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        str(data.get('importe', 0)),
        data.get('metodo_pago', ''),
        0
    ))
    
    estudio_id = cur.lastrowid
    actualizar_proximo_recibo(recibo + 1)
    
    conn.commit()
    conn.close()
    
    return {
        'id': estudio_id,
        'nombre_paciente': data['nombre_paciente'],
        'descripcion': data['descripcion'],
        'recibo': str(recibo),
        'institucion': data.get('institucion', 'REMadom'),
        'cliente': data.get('cliente', ''),
        'fecha': data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        'importe': str(data.get('importe', 0)),
        'metodo_pago': data.get('metodo_pago', ''),
        'procesado': False
    }

def obtener_estudios_pendientes():
    """Obtiene estudios pendientes"""
    conn = sqlite3.connect(DB_PATH)
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
    """Marca como procesado"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE estudios SET procesado = 1 WHERE id = ?", (estudio_id,))
    conn.commit()
    conn.close()
    return True

def health_check():
    """Health check"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM estudios")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM estudios WHERE procesado = 0")
    pendientes = cur.fetchone()[0]
    cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
    proximo = cur.fetchone()[0]
    conn.close()
    
    return {
        'status': 'ok',
        'estudios_totales': total,
        'pendientes': pendientes,
        'proximo_recibo': int(proximo),
        'message': 'DICOX activo (SQLite)'
    }






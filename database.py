import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL no está configurada")
    
    # Render requiere sslmode=require
    if "render.com" in DATABASE_URL and "?sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabla de estudios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estudios (
            id SERIAL PRIMARY KEY,
            nombre_paciente TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            recibo TEXT UNIQUE NOT NULL,
            institucion TEXT DEFAULT 'REMadom',
            cliente TEXT,
            fecha TEXT,
            importe TEXT DEFAULT '0',
            metodo_pago TEXT,
            procesado BOOLEAN DEFAULT FALSE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de configuración (contador global de recibo)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id SERIAL PRIMARY KEY,
            clave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL
        )
    """)
    
    # Inicializar contador si no existe
    cur.execute("""
        INSERT INTO configuracion (clave, valor)
        VALUES ('proximo_recibo', '1')
        ON CONFLICT (clave) DO NOTHING
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

def obtener_proximo_recibo():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Bloqueo para evitar race conditions
    cur.execute("BEGIN")
    cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo' FOR UPDATE")
    row = cur.fetchone()
    proximo = int(row['valor'])
    
    # Actualizar contador
    cur.execute("UPDATE configuracion SET valor = %s WHERE clave = 'proximo_recibo'", (str(proximo + 1),))
    conn.commit()
    
    cur.close()
    conn.close()
    return proximo

def crear_estudio(data):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener próximo recibo
    recibo_numero = obtener_proximo_recibo()
    
    cur.execute("""
        INSERT INTO estudios (
            nombre_paciente, descripcion, recibo, institucion, 
            cliente, fecha, importe, metodo_pago, procesado
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, nombre_paciente, descripcion, recibo, institucion, 
                  cliente, fecha, importe, metodo_pago, procesado
    """, (
        data['nombre_paciente'],
        data['descripcion'],
        str(recibo_numero),
        data.get('institucion', 'REMadom'),
        data.get('cliente', ''),
        data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        str(data.get('importe', 0)),
        data.get('metodo_pago', ''),
        False
    ))
    
    estudio = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return dict(estudio)

def obtener_estudios_pendientes():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estudios WHERE procesado = FALSE ORDER BY id DESC")
    estudios = cur.fetchall()
    
    cur.close()
    conn.close()
    return [dict(e) for e in estudios]

def marcar_procesado(estudio_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE estudios SET procesado = TRUE WHERE id = %s", (estudio_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    return cur.rowcount > 0

def health_check():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM estudios")
    total = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as pendientes FROM estudios WHERE procesado = FALSE")
    pendientes = cur.fetchone()['pendientes']
    
    cur.close()
    conn.close()
    
    return {
        'status': 'ok',
        'estudios_totales': total,
        'pendientes': pendientes,
        'message': 'Servidor DICOX activo'
    }

# Inicializar DB al importar
init_db()

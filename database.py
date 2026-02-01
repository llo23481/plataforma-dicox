import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime
import traceback

# Conexión a PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL no está configurada")

if "render.com" in DATABASE_URL and "?sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Inicializa la base de datos PostgreSQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("🔄 Creando tablas en PostgreSQL...")
        
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
        
        # Tabla de configuración
        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        """)
        
        # Inicializar contador
        cur.execute("""
            INSERT INTO configuracion (clave, valor)
            VALUES ('proximo_recibo', '1')
            ON CONFLICT (clave) DO NOTHING
        """)
        
        conn.commit()
        
        # Verificar
        cur.execute("SELECT * FROM configuracion")
        print(f"✅ Configuración: {cur.fetchone()}")
        
        conn.close()
        print("✅ Base de datos PostgreSQL inicializada")
        
    except Exception as e:
        print(f"❌ Error init_db:")
        traceback.print_exc()
        raise

# Inicializar al importar
init_db()

def obtener_proximo_recibo():
    """Obtiene el próximo recibo"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        row = cur.fetchone()
        conn.close()
        
        if row:
            return int(row['valor'])
        else:
            raise Exception("Contador no encontrado")
    except Exception as e:
        print(f"❌ Error obtener_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def actualizar_proximo_recibo(nuevo_valor):
    """Actualiza el contador"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE configuracion SET valor = %s WHERE clave = 'proximo_recibo'", (str(nuevo_valor),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Error actualizar_proximo_recibo: {e}")
        raise

def crear_estudio(data):
    """Crea un estudio"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        recibo_numero = obtener_proximo_recibo()
        
        cur.execute("""
            INSERT INTO estudios (
                nombre_paciente, descripcion, recibo, institucion, 
                cliente, fecha, importe, metodo_pago, procesado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
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
        
        estudio_id = cur.fetchone()['id']
        actualizar_proximo_recibo(recibo_numero + 1)
        
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
    except Exception as e:
        print(f"❌ Error crear_estudio: {e}")
        traceback.print_exc()
        raise

def obtener_estudios_pendientes():
    """Obtiene estudios pendientes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM estudios WHERE procesado = FALSE ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        
        estudios = []
        for row in rows:
            estudios.append({
                'id': row['id'],
                'nombre_paciente': row['nombre_paciente'],
                'descripcion': row['descripcion'],
                'recibo': row['recibo'],
                'institucion': row['institucion'],
                'cliente': row['cliente'],
                'fecha': row['fecha'],
                'importe': row['importe'],
                'metodo_pago': row['metodo_pago'],
                'procesado': row['procesado']
            })
        
        return estudios
    except Exception as e:
        print(f"❌ Error obtener_estudios_pendientes: {e}")
        raise

def marcar_procesado(estudio_id):
    """Marca como procesado"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE estudios SET procesado = TRUE WHERE id = %s", (estudio_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error marcar_procesado: {e}")
        raise

def health_check():
    """Health check"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM estudios")
        total = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as pendientes FROM estudios WHERE procesado = FALSE")
        pendientes = cur.fetchone()['pendientes']
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        proximo = cur.fetchone()['valor']
        conn.close()
        
        return {
            'status': 'ok',
            'estudios_totales': total,
            'pendientes': pendientes,
            'proximo_recibo': int(proximo),
            'message': 'Servidor DICOX activo (PostgreSQL)'
        }
    except Exception as e:
        print(f"❌ Error health_check: {e}")
        return {'status': 'error', 'message': str(e)}





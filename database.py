import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime
import traceback

# Conexión a PostgreSQL (Render inyecta DATABASE_URL automáticamente)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL and "?sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

print(f"📍 DATABASE_URL configurada: {'SÍ' if DATABASE_URL else 'NO'}")
if DATABASE_URL:
    masked = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
    print(f"   Host: postgres://{masked}")

def get_db():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("✅ Conexión a PostgreSQL exitosa")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar a PostgreSQL:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        traceback.print_exc()
        raise

def init_db():
    """Inicializa la base de datos PostgreSQL"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        print("🔄 Creando tablas...")
        
        # Tabla de estudios - AGREGAR columna estado
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
                numero_aprobacion TEXT DEFAULT '',
                estado TEXT DEFAULT 'pagada',  -- ← AGREGAR ESTA LÍNEA
                procesado BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de configuración (contador global)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
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
        
        # Verificar configuración
        cur.execute("SELECT * FROM configuracion")
        config = cur.fetchone()
        print(f"✅ Configuración inicializada: {dict(config)}")
        
        conn.close()
        print("✅ Base de datos PostgreSQL lista")
        
    except Exception as e:
        print(f"❌ Error en init_db:")
        traceback.print_exc()
        raise

# Inicializar base de datos al importar
print("🚀 Iniciando DICOX Backend (PostgreSQL)...")
init_db()

def obtener_proximo_recibo():
    """Obtiene el próximo número de recibo"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise Exception("Contador 'proximo_recibo' no encontrado")
        
        return int(row['valor'])
    except Exception as e:
        print(f"❌ Error en obtener_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def actualizar_proximo_recibo(nuevo_valor):
    """Actualiza el contador de recibo"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE configuracion SET valor = %s WHERE clave = 'proximo_recibo'", (str(nuevo_valor),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Error en actualizar_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def crear_estudio(data):
    """Crea un nuevo estudio en la base de datos"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Obtener próximo recibo
        recibo_numero = obtener_proximo_recibo()
        
        # Insertar estudio
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
        
        # Actualizar contador
        actualizar_proximo_recibo(recibo_numero + 1)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Estudio creado: Recibo #{recibo_numero}")
        
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
        print(f"❌ Error en crear_estudio: {e}")
        traceback.print_exc()
        raise

def obtener_estudios_pendientes():
    """Obtiene todos los estudios (sin filtrar por procesado)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM estudios ORDER BY id DESC")
        estudios = cur.fetchall()
        conn.close()
        
        # Asegurar que todos los estudios tengan estado (por compatibilidad)
        for estudio in estudios:
            if 'estado' not in estudio:
                estudio['estado'] = 'pagada'
        
        return estudios
    except Exception as e:
        print(f"❌ Error en obtener_estudios_pendientes: {e}")
        traceback.print_exc()
        raise

def marcar_procesado(estudio_id):
    """Marca un estudio como procesado"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE estudios SET procesado = TRUE WHERE id = %s", (estudio_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error en marcar_procesado: {e}")
        traceback.print_exc()
        raise

def health_check():
    """Verifica el estado de la base de datos"""
    try:
        conn = get_db()
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
            'message': 'DICOX activo (PostgreSQL)'
        }
    except Exception as e:
        print(f"❌ Error en health_check: {e}")
        return {'status': 'error', 'message': str(e)}

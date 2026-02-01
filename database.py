import sqlite3
import os
import time
from datetime import datetime
import traceback

# Ruta persistente en Render
DB_PATH = '/opt/render/project/src/data/estudios.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

print(f"📍 Base de datos: {DB_PATH}")

def init_db():
    """Inicializa la base de datos SQLite con configuración robusta"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
        cur = conn.cursor()
        
        print("🔄 Creando tablas...")
        
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
        
        # Verificar
        cur.execute("SELECT * FROM configuracion")
        config = cur.fetchone()
        print(f"✅ Configuración: {config}")
        
        conn.close()
        print("✅ Base de datos SQLite inicializada")
        
    except Exception as e:
        print(f"❌ Error init_db:")
        traceback.print_exc()
        raise

# Inicializar al importar
init_db()

def get_connection():
    """Obtiene una conexión a la base de datos con timeout"""
    return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)

def execute_with_retry(query, params=(), max_retries=5):
    """Ejecuta una consulta con reintentos automáticos en caso de bloqueo"""
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            result = cur.fetchall()
            conn.commit()
            conn.close()
            return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"⚠️ Base de datos bloqueada, reintentando ({attempt + 1}/{max_retries})...")
                time.sleep(0.1 * (attempt + 1))  # Espera exponencial
                continue
            else:
                raise
        except Exception as e:
            print(f"❌ Error en execute_with_retry: {e}")
            traceback.print_exc()
            raise

def obtener_proximo_recibo():
    """Obtiene el próximo número de recibo con manejo de bloqueos"""
    try:
        print("🔍 Obteniendo próximo recibo...")
        result = execute_with_retry(
            "SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'"
        )
        if result:
            valor = int(result[0][0])
            print(f"✅ Próximo recibo: {valor}")
            return valor
        else:
            raise Exception("Contador de recibo no encontrado")
    except Exception as e:
        print(f"❌ Error obtener_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def actualizar_proximo_recibo(nuevo_valor):
    """Actualiza el contador con manejo de bloqueos"""
    try:
        print(f"📝 Actualizando contador a: {nuevo_valor}")
        execute_with_retry(
            "UPDATE configuracion SET valor = ? WHERE clave = 'proximo_recibo'",
            (str(nuevo_valor),)
        )
        print(f"✅ Contador actualizado correctamente")
    except Exception as e:
        print(f"❌ Error actualizar_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def crear_estudio(data):
    """Crea un estudio con manejo robusto de bloqueos"""
    try:
        print(f"🆕 Creando nuevo estudio...")
        
        # Obtener próximo recibo
        recibo_numero = obtener_proximo_recibo()
        
        # Insertar estudio
        execute_with_retry("""
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
        
        # Actualizar contador
        actualizar_proximo_recibo(recibo_numero + 1)
        
        print(f"✅ Estudio creado con recibo: {recibo_numero}")
        
        return {
            'id': recibo_numero,  # Usamos el recibo como ID temporal
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
        print(f"📋 Obteniendo estudios pendientes...")
        result = execute_with_retry(
            "SELECT * FROM estudios WHERE procesado = 0 ORDER BY id DESC"
        )
        
        estudios = []
        for row in result:
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
        
        print(f"✅ Se encontraron {len(estudios)} estudios pendientes")
        return estudios
        
    except Exception as e:
        print(f"❌ Error obtener_estudios_pendientes: {e}")
        traceback.print_exc()
        raise

def marcar_procesado(estudio_id):
    """Marca un estudio como procesado"""
    try:
        print(f"✅ Marcando estudio {estudio_id} como procesado...")
        execute_with_retry(
            "UPDATE estudios SET procesado = 1 WHERE id = ?",
            (estudio_id,)
        )
        print(f"✅ Estudio {estudio_id} marcado como procesado")
        return True
    except Exception as e:
        print(f"❌ Error marcar_procesado: {e}")
        traceback.print_exc()
        raise

def health_check():
    """Verifica el estado de la base de datos"""
    try:
        print(f"🏥 Health check...")
        total_result = execute_with_retry("SELECT COUNT(*) FROM estudios")
        total = total_result[0][0]
        
        pendientes_result = execute_with_retry("SELECT COUNT(*) FROM estudios WHERE procesado = 0")
        pendientes = pendientes_result[0][0]
        
        proximo_result = execute_with_retry("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        proximo = int(proximo_result[0][0])
        
        print(f"✅ Health check completado: {total} totales, {pendientes} pendientes, próximo: {proximo}")
        
        return {
            'status': 'ok',
            'estudios_totales': total,
            'pendientes': pendientes,
            'proximo_recibo': proximo,
            'message': 'Servidor DICOX activo (SQLite + manejo de bloqueos)'
        }
        
    except Exception as e:
        print(f"❌ Error en health_check: {e}")
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e)
        }







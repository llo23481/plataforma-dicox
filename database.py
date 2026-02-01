import sqlite3
import os
from datetime import datetime
import traceback

# Ruta SIMPLE (relativa al archivo)
DB_PATH = 'data/estudios.db'
os.makedirs('data', exist_ok=True)

print(f"📍 Base de datos: {DB_PATH}")

def init_db():
    """Inicializa la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
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
        
        # Tabla de configuración
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
        print(f"✅ Configuración: {cur.fetchone()}")
        
        conn.close()
        print("✅ Base de datos inicializada")
        
    except Exception as e:
        print(f"❌ Error init_db:")
        traceback.print_exc()
        raise

# Inicializar al importar
init_db()

def obtener_proximo_recibo():
    """Obtiene el próximo recibo"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        row = cur.fetchone()
        conn.close()
        
        if row:
            return int(row[0])
        else:
            raise Exception("Contador no encontrado")
    except Exception as e:
        print(f"❌ Error obtener_proximo_recibo: {e}")
        traceback.print_exc()
        raise

def actualizar_proximo_recibo(nuevo_valor):
    """Actualiza el contador"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE configuracion SET valor = ? WHERE clave = 'proximo_recibo'", (str(nuevo_valor),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Error actualizar_proximo_recibo: {e}")
        raise

def crear_estudio(data):
    """Crea un estudio"""
    try:
        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"❌ Error obtener_estudios_pendientes: {e}")
        raise

def marcar_procesado(estudio_id):
    """Marca como procesado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE estudios SET procesado = 1 WHERE id = ?", (estudio_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error marcar_procesado: {e}")
        raise

def health_check():
    """Health check"""
    try:
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
            'message': 'Servidor DICOX activo'
        }
    except Exception as e:
        print(f"❌ Error health_check: {e}")
        return {'status': 'error', 'message': str(e)}




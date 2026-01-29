from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Archivo de base de datos persistente
DB_FILE = 'estudios_db.json'

def cargar_estudios():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_estudios(estudios):
    with open(DB_FILE, 'w') as f:
        json.dump(estudios, f, indent=2)

@app.route('/api/crear-estudio', methods=['POST'])
def crear_estudio_api():
    try:
        data = request.get_json()
        
        if not data.get('nombre_paciente') or not data.get('descripcion'):
            return jsonify({
                'success': False,
                'message': 'Faltan datos obligatorios'
            }), 400
        
        estudio = {
            'id': len(cargar_estudios()) + 1,
            'nombre_paciente': data['nombre_paciente'],
            'descripcion': data['descripcion'],
            'recibo': data.get('recibo', 'N/A'),
            'institucion': data.get('institucion', 'REMadom'),
            'cliente': data.get('cliente', ''),
            'fecha': data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
            'importe': data.get('importe', 0),
            'metodo_pago': data.get('metodo_pago', ''),
            'timestamp': datetime.now().isoformat(),
            'procesado': False
        }
        
        estudios = cargar_estudios()
        estudios.append(estudio)
        guardar_estudios(estudios)
        
        print(f"\n{'='*70}")
        print(f" 📤 NUEVO ESTUDIO RECIBIDO")
        print(f"{'='*70}")
        print(f" 👤 Paciente : {estudio['nombre_paciente']}")
        print(f" 📋 Descripción : {estudio['descripcion']}")
        print(f" 🎫 Recibo : {estudio['recibo']}")
        print(f" 🏢 Institución : {estudio['institucion']}")
        print(f" 💰 Importe : RD${estudio['importe']}")
        print(f" 📊 Total en DB: {len(estudios)}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'message': 'Estudio creado correctamente',
            'estudio': estudio
        }), 201
        
    except Exception as e:
        print(f"Error al crear estudio: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error del servidor: {str(e)}'
        }), 500

@app.route('/api/estudios-pendientes', methods=['GET'])
def obtener_estudios_pendientes():
    try:
        estudios = cargar_estudios()
        pendientes = [e for e in estudios if not e.get('procesado', False)]
        
        print(f"[API] Consulta de pendientes - Total: {len(estudios)}, Pendientes: {len(pendientes)}")
        
        return jsonify({
            'success': True,
            'estudios': pendientes,
            'total': len(pendientes)
        }), 200
    except Exception as e:
        print(f"[API ERROR] {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcar-procesado/<int:estudio_id>', methods=['POST'])
def marcar_procesado(estudio_id):
    try:
        estudios = cargar_estudios()
        for estudio in estudios:
            if estudio.get('id') == estudio_id:
                estudio['procesado'] = True
                guardar_estudios(estudios)
                print(f"[API] ✅ Estudio {estudio_id} marcado como procesado")
                return jsonify({'success': True}), 200
        return jsonify({'success': False, 'message': 'Estudio no encontrado'}), 404
    except Exception as e:
        print(f"[API ERROR] {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    estudios = cargar_estudios()
    pendientes = len([e for e in estudios if not e.get('procesado', False)])
    return jsonify({
        'status': 'ok',
        'estudios_totales': len(estudios),
        'pendientes': pendientes,
        'message': 'Servidor DICOX activo'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 SERVIDOR DICOX INICIADO")
    print(f"   URL: http://localhost:{port}")
    print(f"   API: http://localhost:{port}/api/crear-estudio\n")
    app.run(host='0.0.0.0', port=port, debug=False)


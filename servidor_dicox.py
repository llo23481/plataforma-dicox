from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from database import crear_estudio, obtener_estudios_pendientes, marcar_procesado, health_check, obtener_proximo_recibo

app = Flask(__name__)
CORS(app)

@app.route('/api/proximo-recibo', methods=['GET'])
def api_proximo_recibo():
    """Obtiene el próximo recibo"""
    try:
        print("📥 GET /api/proximo-recibo")
        proximo = obtener_proximo_recibo()
        print(f"✅ Próximo recibo: {proximo}")
        return jsonify({'success': True, 'proximo_recibo': proximo}), 200
    except Exception as e:
        print(f"❌ Error /api/proximo-recibo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crear-estudio', methods=['POST'])
def crear_estudio_api():
    """Crea un estudio"""
    try:
        print("📥 POST /api/crear-estudio")
        data = request.get_json()
        
        if not data.get('nombre_paciente') or not data.get('descripcion'):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        
        estudio = crear_estudio(data)
        print(f"✅ Estudio creado: {estudio['recibo']}")
        
        return jsonify({'success': True, 'estudio': estudio}), 201
    except Exception as e:
        print(f"❌ Error /api/crear-estudio: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estudios-pendientes', methods=['GET'])
def obtener_estudios_pendientes_api():
    """Obtiene estudios pendientes"""
    try:
        print("📥 GET /api/estudios-pendientes")
        estudios = obtener_estudios_pendientes()
        print(f"✅ {len(estudios)} estudios pendientes")
        return jsonify({'success': True, 'estudios': estudios}), 200
    except Exception as e:
        print(f"❌ Error /api/estudios-pendientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcar-procesado/<int:estudio_id>', methods=['POST'])
def marcar_procesado_api(estudio_id):
    """Marca como procesado"""
    try:
        print(f"📥 POST /api/marcar-procesado/{estudio_id}")
        marcar_procesado(estudio_id)
        print(f"✅ Estudio {estudio_id} procesado")
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"❌ Error /api/marcar-procesado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    try:
        print("📥 GET /api/health")
        result = health_check()
        print(f"✅ Health: {result}")
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error /api/health: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 SERVIDOR DICOX INICIADO")
    print(f"   Puerto: {port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)





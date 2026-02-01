from flask import Flask, request, jsonify
from flask_cors import CORS
from database import crear_estudio, obtener_estudios_pendientes, marcar_procesado, health_check, obtener_proximo_recibo

app = Flask(__name__)
CORS(app)

@app.route('/api/proximo-recibo', methods=['GET'])
def api_proximo_recibo():
    try:
        return jsonify({'success': True, 'proximo_recibo': obtener_proximo_recibo()}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crear-estudio', methods=['POST'])
def api_crear_estudio():
    try:
        data = request.get_json()
        if not data.get('nombre_paciente') or not data.get('descripcion'):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        return jsonify({'success': True, 'estudio': crear_estudio(data)}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estudios-pendientes', methods=['GET'])
def api_estudios_pendientes():
    try:
        return jsonify({'success': True, 'estudios': obtener_estudios_pendientes()}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcar-procesado/<int:estudio_id>', methods=['POST'])
def api_marcar_procesado(estudio_id):
    try:
        marcar_procesado(estudio_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    try:
        return jsonify(health_check()), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500






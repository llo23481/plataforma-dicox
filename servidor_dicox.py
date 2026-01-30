from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from database import crear_estudio, obtener_estudios_pendientes, marcar_procesado, health_check

app = Flask(__name__)
CORS(app)

@app.route('/api/proximo-recibo', methods=['GET'])
def api_proximo_recibo():
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'proximo_recibo'")
        row = cur.fetchone()
        proximo = int(row['valor'])
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'proximo_recibo': proximo}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crear-estudio', methods=['POST'])
def crear_estudio_api():
    try:
        data = request.get_json()
        
        if not data.get('nombre_paciente') or not data.get('descripcion'):
            return jsonify({
                'success': False,
                'message': 'Faltan datos obligatorios'
            }), 400
        
        estudio = crear_estudio(data)
        
        print(f"\n{'='*70}")
        print(f" 📤 NUEVO ESTUDIO RECIBIDO")
        print(f"{'='*70}")
        print(f" 👤 Paciente : {estudio['nombre_paciente']}")
        print(f" 📋 Descripción : {estudio['descripcion']}")
        print(f" 🎫 Recibo : {estudio['recibo']}")
        print(f" 🏢 Institución : {estudio['institucion']}")
        print(f" 💰 Importe : RD${estudio['importe']}")
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
def obtener_estudios_pendientes_api():
    try:
        estudios = obtener_estudios_pendientes()
        return jsonify({
            'success': True,
            'estudios': estudios,
            'total': len(estudios)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcar-procesado/<int:estudio_id>', methods=['POST'])
def marcar_procesado_api(estudio_id):
    try:
        if marcar_procesado(estudio_id):
            print(f"[API] ✅ Estudio {estudio_id} marcado como procesado")
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'message': 'Estudio no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    try:
        return jsonify(health_check()), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 SERVIDOR DICOX INICIADO")
    print(f"   URL: http://localhost:{port}")
    print(f"   API: http://localhost:{port}/api/crear-estudio\n")
    app.run(host='0.0.0.0', port=port, debug=False)




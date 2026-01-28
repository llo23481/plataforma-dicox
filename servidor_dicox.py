from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
estudios_pendientes = []

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
            'nombre_paciente': data['nombre_paciente'],
            'descripcion': data['descripcion'],
            'recibo': data.get('recibo', 'N/A'),
            'institucion': data.get('institucion', 'REMadom'),
            'cliente': data.get('cliente', ''),
            'fecha': data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
            'importe': data.get('importe', 0),
            'metodo_pago': data.get('metodo_pago', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        estudios_pendientes.append(estudio)
        
        print(f"\n{'='*70}")
        print(f" 📤 NUEVO ESTUDIO RECIBIDO")
        print(f"{'='*70}")
        print(f" 👤 Paciente : {estudio['nombre_paciente']}")
        print(f" 📋 Descripción : {estudio['descripcion']}")
        print(f" 🎫 Recibo : {estudio['recibo']}")
        print(f" 🏢 Institución : {estudio['institucion']}")
        print(f" 📅 Fecha : {estudio['fecha']}")
        print(f" 💰 Importe : RD${estudio['importe']}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'message': 'Estudio recibido correctamente',
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
    return jsonify({
        'success': True,
        'estudios': estudios_pendientes
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Servidor DICOX activo'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 SERVIDOR DICOX INICIADO")
    print(f"   URL: http://localhost:{port}")
    print(f"   API: http://localhost:{port}/api/crear-estudio\n")
    app.run(host='0.0.0.0', port=port, debug=False)

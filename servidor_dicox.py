from flask import Flask, request, jsonify
from flask_cors import CORS
from database import crear_estudio, obtener_estudios_pendientes, marcar_procesado, health_check, obtener_proximo_recibo, get_db

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

@app.route('/api/actualizar-estudio/<int:estudio_id>', methods=['PUT'])
def actualizar_estudio(estudio_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar que el estudio exista
        cur.execute("SELECT id FROM estudios WHERE id = %s", (estudio_id,))
        if not cur.fetchone():
            return jsonify({
                'success': False,
                'message': 'Estudio no encontrado'
            }), 404
        
        # Actualizar estudio
        cur.execute("""
            UPDATE estudios
            SET nombre_paciente = %s,
                descripcion = %s,
                cliente = %s,
                fecha = %s,
                importe = %s,
                metodo_pago = %s,
                numero_aprobacion = %s
            WHERE id = %s
        """, (
            data.get('nombre_paciente'),
            data.get('descripcion'),
            data.get('cliente'),
            data.get('fecha'),
            str(data.get('importe', 0)),
            data.get('metodo_pago'),
            data.get('numero_aprobacion', ''),
            estudio_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Estudio actualizado correctamente',
            'estudio_id': estudio_id
        })
        
    except Exception as e:
        print(f"❌ Error al actualizar estudio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
@app.route('/api/anular-estudio/<int:estudio_id>', methods=['PUT'])
def api_anular_estudio(estudio_id):
    try:
        print(f"🔄 Anulando estudio ID: {estudio_id}")
        
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar que el estudio exista
        cur.execute("SELECT id FROM estudios WHERE id = %s", (estudio_id,))
        if not cur.fetchone():
            return jsonify({
                'success': False,
                'message': f'Estudio ID {estudio_id} no encontrado'
            }), 404
        
        # Actualizar estado a 'anulada' Y importe a 0
        cur.execute("""
            UPDATE estudios
            SET estado = 'anulada',
                importe = '0'
            WHERE id = %s
        """, (estudio_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Estudio ID {estudio_id} anulado correctamente (importe = 0)")
        
        return jsonify({
            'success': True,
            'message': 'Estudio anulado correctamente',
            'estudio_id': estudio_id
        })
        
    except Exception as e:
        print(f"❌ Error al anular estudio ID {estudio_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

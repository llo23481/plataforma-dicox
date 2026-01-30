from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from database import SessionLocal, Estudio, Configuracion

app = Flask(__name__)
CORS(app)

def obtener_proximo_recibo():
    """Obtiene y actualiza el próximo número de recibo desde la BD global"""
    db = SessionLocal()
    try:
        config = db.query(Configuracion).filter(Configuracion.clave == "proximo_recibo").first()
        if not config:
            # Inicializar si no existe
            config = Configuracion(clave="proximo_recibo", valor="1")
            db.add(config)
            db.commit()
            return 1
        
        proximo = int(config.valor)
        config.valor = str(proximo + 1)
        db.commit()
        return proximo
    finally:
        db.close()

@app.route('/api/proximo-recibo', methods=['GET'])
def obtener_proximo_recibo_api():
    """Endpoint para que la web obtenga el próximo número de recibo"""
    try:
        proximo = obtener_proximo_recibo()
        # Restaurar el valor (no lo incrementamos aún, solo lo consultamos)
        db = SessionLocal()
        config = db.query(Configuracion).filter(Configuracion.clave == "proximo_recibo").first()
        config.valor = str(proximo)
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'proximo_recibo': proximo
        }), 200
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
        
        # Obtener próximo recibo de la BD global (esto incrementa el contador)
        recibo_numero = obtener_proximo_recibo()
        
        estudio = Estudio(
            nombre_paciente=data['nombre_paciente'],
            descripcion=data['descripcion'],
            recibo=str(recibo_numero),
            institucion=data.get('institucion', 'REMadom'),
            cliente=data.get('cliente', ''),
            fecha=data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
            importe=str(data.get('importe', 0)),
            metodo_pago=data.get('metodo_pago', ''),
            procesado=False
        )
        
        db = SessionLocal()
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        
        print(f"\n{'='*70}")
        print(f" 📤 NUEVO ESTUDIO RECIBIDO")
        print(f"{'='*70}")
        print(f" 👤 Paciente : {estudio.nombre_paciente}")
        print(f" 📋 Descripción : {estudio.descripcion}")
        print(f" 🎫 Recibo : {estudio.recibo}")
        print(f" 🏢 Institución : {estudio.institucion}")
        print(f" 💰 Importe : RD${estudio.importe}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'message': 'Estudio creado correctamente',
            'estudio': {
                'id': estudio.id,
                'nombre_paciente': estudio.nombre_paciente,
                'descripcion': estudio.descripcion,
                'recibo': estudio.recibo,
                'institucion': estudio.institucion,
                'cliente': estudio.cliente,
                'fecha': estudio.fecha,
                'importe': estudio.importe,
                'metodo_pago': estudio.metodo_pago,
                'procesado': estudio.procesado
            }
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
        db = SessionLocal()
        estudios = db.query(Estudio).filter(Estudio.procesado == False).all()
        
        estudios_list = []
        for e in estudios:
            estudios_list.append({
                'id': e.id,
                'nombre_paciente': e.nombre_paciente,
                'descripcion': e.descripcion,
                'recibo': e.recibo,
                'institucion': e.institucion,
                'cliente': e.cliente,
                'fecha': e.fecha,
                'importe': e.importe,
                'metodo_pago': e.metodo_pago
            })
        
        return jsonify({
            'success': True,
            'estudios': estudios_list,
            'total': len(estudios_list)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcar-procesado/<int:estudio_id>', methods=['POST'])
def marcar_procesado(estudio_id):
    try:
        db = SessionLocal()
        estudio = db.query(Estudio).filter(Estudio.id == estudio_id).first()
        
        if estudio:
            estudio.procesado = True
            db.commit()
            print(f"[API] ✅ Estudio {estudio_id} marcado como procesado")
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'message': 'Estudio no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    db = SessionLocal()
    total = db.query(Estudio).count()
    pendientes = db.query(Estudio).filter(Estudio.procesado == False).count()
    db.close()
    
    return jsonify({
        'status': 'ok',
        'estudios_totales': total,
        'pendientes': pendientes,
        'message': 'Servidor DICOX activo'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 SERVIDOR DICOX INICIADO")
    print(f"   URL: http://localhost:{port}")
    print(f"   API: http://localhost:{port}/api/crear-estudio\n")
    app.run(host='0.0.0.0', port=port, debug=False)



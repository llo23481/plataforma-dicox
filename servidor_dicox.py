# servidor_dicox.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuración de base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///dicox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de estudio
class EstudioWeb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_paciente = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    recibo = db.Column(db.String(50), unique=True, nullable=False)
    institucion = db.Column(db.String(100), default="REMadom")
    cliente = db.Column(db.String(255))
    fecha = db.Column(db.String(10))  # AAAA-MM-DD
    sincronizado = db.Column(db.Boolean, default=False)

# Endpoint para crear estudios
@app.route('/api/crear-estudio', methods=['POST'])
def crear_estudio():
    try:
        data = request.json
        if not data or 'nombre_paciente' not in data or 'recibo' not in data:
            return jsonify({"success": False, "message": "Datos incompletos"}), 400
            
        estudio = EstudioWeb(
            nombre_paciente=data['nombre_paciente'],
            descripcion=data.get('descripcion', ''),
            recibo=str(data['recibo']),
            institucion=data.get('institucion', 'REMadom'),
            cliente=data.get('cliente', ''),
            fecha=data.get('fecha', '')
        )
        db.session.add(estudio)
        db.session.commit()
        return jsonify({"success": True, "id": estudio.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Endpoint para obtener estudios no sincronizados
@app.route('/api/estudios')
def obtener_estudios():
    sync_param = request.args.get('sincronizado')
    if sync_param == 'false':
        estudios = EstudioWeb.query.filter_by(sincronizado=False).all()
    else:
        estudios = EstudioWeb.query.all()
        
    return jsonify([{
        'id': e.id,
        'nombre_paciente': e.nombre_paciente,
        'descripcion': e.descripcion,
        'recibo': e.recibo,
        'institucion': e.institucion,
        'fecha': e.fecha
    } for e in estudios])

# Endpoint para marcar como sincronizados
@app.route('/api/marcar-sincronizados', methods=['POST'])
def marcar_sincronizados():
    try:
        data = request.json
        ids = data.get('ids', [])
        if ids:
            EstudioWeb.query.filter(EstudioWeb.id.in_(ids)).update({'sincronizado': True})
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Inicializar base de datos
@app.before_first_request
def crear_tablas():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)


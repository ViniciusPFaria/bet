from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import random
import re

# Initialize SQLAlchemy without app first
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure PostgreSQL connection using Railway provided URL
    # Get database URL from environment or use the Railway template
    database_url = os.getenv('DATABASE_URL', '${{ Postgres.DATABASE_URL }}')
    
    # If the URL starts with postgres:// (Railway format), convert to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Configure SQLAlchemy to use pg8000 as the driver
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Create all tables within app context
    with app.app_context():
        db.create_all()
    
    return app

# Create the Flask application
app = create_app()

# Define Participant model
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    funcao = db.Column(db.String(100), nullable=False)
    segmento = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Participant {self.nome}>'

# Página de cadastro
@app.route("/")
def cadastro():
    return render_template("cadastro.html")

# Health check endpoint for Railway
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# Endpoint para cadastrar participantes
@app.route("/api/cadastro", methods=["POST"])
def cadastrar():
    data = request.json
    nome = data["nome"]
    empresa = data["empresa"]
    funcao = data["funcao"]
    segmento = data["segmento"]
    email = data["email"]

    # Check if participant with this email already exists
    existing_participant = Participant.query.filter_by(email=email).first()
    if existing_participant:
        return jsonify({"success": False, "message": "Email já cadastrado"})

    # Create new participant
    new_participant = Participant(
        nome=nome,
        empresa=empresa,
        funcao=funcao,
        segmento=segmento,
        email=email
    )
    
    # Add to database
    db.session.add(new_participant)
    db.session.commit()

    return jsonify({"success": True})

# Página de confirmação
@app.route("/confirmacao")
def confirmacao():
    return render_template("confirmacao.html")

# Rota para sortear um vencedor
@app.route("/sorteio")
def sorteio():
    # Get all participants from the database
    participants = Participant.query.all()
    participantes = [p.nome for p in participants]

    vencedor = random.choice(participantes) if participantes else "Nenhum participante cadastrado"

    return render_template("vencedor.html", vencedor=vencedor)

# Página do vencedor
@app.route("/vencedor")
def vencedor():
    return render_template("vencedor.html", vencedor="Aguardando sorteio")

if __name__ == "__main__":
    app.run(debug=True)

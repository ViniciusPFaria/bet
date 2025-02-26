from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import random

app = Flask(__name__)

# Configure PostgreSQL connection using Railway provided URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', '${{ Postgres.DATABASE_URL }}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

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

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()

# Página de cadastro
@app.route("/")
def cadastro():
    return render_template("cadastro.html")

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

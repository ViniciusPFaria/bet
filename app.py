from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from flask_cors import CORS
import os
import random
import time

# Create the Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configure PostgreSQL connection
database_url = os.environ.get('DATABASE_URL')

# Check if the URL is the template variable (not replaced)
if database_url and ('${{' in database_url or '}}' in database_url):
    print(f"WARNING: DATABASE_URL contains template variables that weren't replaced: {database_url}")
    print("Falling back to SQLite database")
    database_url = "sqlite:///participants.db"

# Fallback for missing database URL
if not database_url:
    print("WARNING: No DATABASE_URL found in environment, using SQLite database")
    database_url = "sqlite:///participants.db"

# Ensure correct URL format for PostgreSQL
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
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

# Health check endpoint - simplest possible
@app.route("/health")
def health():
    try:
        # Try a simple database query to make sure connection works
        Participant.query.limit(1).all()
        return "OK - Database connected"
    except Exception as e:
        # Don't fail health check on DB error to allow app to start
        print(f"Health check warning: {str(e)}")
        return "OK - Application running, but database not connected", 200

# Basic root endpoint
@app.route("/")
def index():
    try:
        return render_template("cadastro.html")
    except Exception as e:
        return f"App is running, but there was an error: {str(e)}"

# Página de cadastro
@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

# Endpoint para cadastrar participantes
@app.route("/api/cadastro", methods=["POST"])
def cadastrar():
    try:
        # Log request data for debugging
        print(f"Received POST request with data: {request.data}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
            print("Received JSON data")
        else:
            data = request.form
            print("Received form data")
        
        # Extract form fields
        nome = data.get("nome")
        empresa = data.get("empresa")
        funcao = data.get("funcao")
        segmento = data.get("segmento")
        email = data.get("email")
        
        print(f"Parsed data: nome={nome}, empresa={empresa}, funcao={funcao}, segmento={segmento}, email={email}")
        
        # Validate required fields
        if not all([nome, empresa, funcao, segmento, email]):
            return jsonify({"success": False, "message": "Todos os campos são obrigatórios"}), 400

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
        
        print(f"Successfully registered user: {nome}")
        return jsonify({"success": True, "message": "Cadastro realizado com sucesso!"})
    except Exception as e:
        print(f"Error in /api/cadastro: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Preflighted CORS request handler
@app.route("/api/cadastro", methods=["OPTIONS"])
def cadastrar_preflight():
    return "", 200

# Página de confirmação
@app.route("/confirmacao")
def confirmacao():
    return render_template("confirmacao.html")

# Rota para sortear um vencedor
@app.route("/sorteio")
def sorteio():
    try:
        # Get all participants from the database
        participants = Participant.query.all()
        participantes = [p.nome for p in participants]

        vencedor = random.choice(participantes) if participantes else "Nenhum participante cadastrado"

        return render_template("vencedor.html", vencedor=vencedor)
    except Exception as e:
        return f"Error in sorteio: {str(e)}", 500

# Página do vencedor
@app.route("/vencedor")
def vencedor():
    return render_template("vencedor.html", vencedor="Aguardando sorteio")

# Create database tables with retry mechanism
def create_tables_with_retry(retries=5, delay=5):
    with app.app_context():
        for attempt in range(retries):
            try:
                print(f"Attempt {attempt+1}/{retries} to create database tables")
                db.create_all()
                print("Database tables created successfully!")
                return True
            except Exception as e:
                print(f"Error creating tables: {str(e)}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("Failed to create tables after all attempts")
                    return False

# Only call this when explicitly running this file
if __name__ == "__main__":
    # Create database tables
    create_tables_with_retry()
    app.run(debug=True)

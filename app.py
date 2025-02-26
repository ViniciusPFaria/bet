from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import random

# Create the Flask application
app = Flask(__name__)

# Configure PostgreSQL connection
# IMPORTANT: On Railway, set DATABASE_URL in the environment variables section
# Do not use the template format in the code
database_url = os.environ.get('DATABASE_URL')

# Fallback for local development (this won't be used on Railway)
if not database_url:
    print("WARNING: No DATABASE_URL found in environment, using development database")
    database_url = "sqlite:///participants.db"

# Ensure correct URL format if it's a PostgreSQL URL
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Add pg8000 driver parameter only for PostgreSQL URLs, not for SQLite
if database_url and 'postgresql://' in database_url:
    if '?' not in database_url:
        database_url += '?driver=pg8000'
    else:
        database_url += '&driver=pg8000'

# Safety: Don't print full URL as it contains password
if database_url and '@' in database_url:
    print(f"Database URL (without password): {database_url.split('@')[0]}@...")
else:
    print(f"Using database: {database_url}")

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
        return f"Error connecting to database: {str(e)}", 500

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
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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

# Function to create database tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            raise

# Only call this when explicitly running this file
if __name__ == "__main__":
    # Create database tables
    init_db()
    app.run(debug=True)

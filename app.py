from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from flask_cors import CORS
import os
import random
import time
from sqlalchemy import create_engine

# Create the Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Get MySQL connection details from environment variables (Railway)
mysql_user = os.environ.get('MYSQLUSER', 'root')
mysql_password = os.environ.get('MYSQLPASSWORD', 'ILKRkbCNCrcYWftbRSK1kjtAjWFQDelJ')
mysql_host = os.environ.get('MYSQLHOST', 'mysql.railway.internal')
mysql_port = os.environ.get('MYSQLPORT', '3306')
mysql_database = os.environ.get('MYSQLDATABASE', 'railway')

# Build MySQL connection string
database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

# Fall back to SQLite for local development if MySQL variables aren't set
if not all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_database]):
    database_url = "sqlite:///participants.db"
    print(f"Using SQLite database for local development: {database_url}")
else:
    print(f"Using MySQL database: {mysql_database} on {mysql_host}")

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

# Define Participant model
class Participant(db.Model):
    __tablename__ = 'participant'
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
    # Always return 200 during startup to allow the container to initialize
    return "OK - Application running", 200

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
        
        # If no participants found, try to seed the database
        if not participants:
            print("No participants found in database, attempting to seed from code.txt...")
            try:
                from seed_db import seed_database
                with app.app_context():
                    seed_success = seed_database()
                    if seed_success:
                        # Query again after seeding
                        participants = Participant.query.all()
                        print(f"Database seeded successfully, now has {len(participants)} participants")
                    else:
                        print("Database seeding failed")
            except Exception as seed_error:
                print(f"Error while trying to seed database: {str(seed_error)}")
        
        # After potential seeding, check participants again
        if not participants:
            return render_template("vencedor.html", 
                                  vencedor="Nenhum participante cadastrado. Por favor, verifique o banco de dados.", 
                                  index="0",
                                  error="Database is empty. Please ensure code.txt is properly formatted and accessible.")
        
        # Choose a random winner and get their index in the list
        winner_index = random.randint(0, len(participants) - 1)
        vencedor = participants[winner_index].nome
        
        # The index to display is 1-based for better user experience
        display_index = winner_index + 1

        return render_template("vencedor.html", vencedor=vencedor, index=display_index)
    except Exception as e:
        print(f"Error in sorteio route: {str(e)}")
        return render_template("vencedor.html", 
                              vencedor="Erro ao processar o sorteio", 
                              index="?",
                              error=str(e))

# Página do vencedor
@app.route("/vencedor")
def vencedor():
    return render_template("vencedor.html", vencedor="Aguardando sorteio", index="?")

# Página para listar todos os participantes
@app.route("/participantes")
def participantes():
    try:
        participants = Participant.query.all()
        
        # If no participants found, try to seed the database
        if not participants:
            print("No participants found in database, attempting to seed from code.txt...")
            try:
                from seed_db import seed_database
                with app.app_context():
                    seed_success = seed_database()
                    if seed_success:
                        # Query again after seeding
                        participants = Participant.query.all()
                        print(f"Database seeded successfully, now has {len(participants)} participants")
                    else:
                        print("Database seeding failed")
            except Exception as seed_error:
                print(f"Error while trying to seed database: {str(seed_error)}")
        
        return render_template("participantes.html", participants=participants)
    except Exception as e:
        print(f"Error retrieving participants: {str(e)}")
        return render_template("participantes.html", 
                              participants=[],
                              error=f"Error retrieving participants: {str(e)}")

# Special route to seed database from code.txt
@app.route("/api/seed", methods=["GET"])
def seed_database_route():
    try:
        # Import the seed function dynamically to avoid circular imports
        from seed_db import seed_database
        
        with app.app_context():
            success = seed_database()
            
        if success:
            return jsonify({
                "success": True,
                "message": "Database has been seeded successfully",
                "participant_count": Participant.query.count()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to seed database. Check server logs for details."
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Create database tables with retry mechanism
def create_tables_with_retry(retries=5, delay=5):
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt+1}/{retries} to create database tables")
            db.create_all()
            print("Database tables created successfully!")
            return True
        except Exception as e:
            print(f"Error creating tables: {type(e).__name__}: {str(e)}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Failed to create tables after all attempts")
                return False

# Function to initialize the database
def init_db():
    return create_tables_with_retry()

# Initialize the database tables
with app.app_context():
    create_tables_with_retry()

# Only call this when explicitly running this file
if __name__ == "__main__":
    app.run(debug=True)

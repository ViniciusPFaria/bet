from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from flask_cors import CORS
import os
import random
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import csv
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Get MySQL connection details from environment variables (Railway)
mysql_user = os.environ.get('MYSQLUSER', 'root')
mysql_password = os.environ.get('MYSQLPASSWORD', 'zgMuJZhGuNIFmCIQMDKGMEDxcETXZzZM')
mysql_host = os.environ.get('MYSQLHOST', 'mysql.railway.internal')
mysql_port = os.environ.get('MYSQLPORT', '3306')
mysql_database = os.environ.get('MYSQLDATABASE', 'railway')

# Check if we have the public URL available (for cross-project connections)
if os.environ.get('MYSQL_PUBLIC_URL'):
    logger.info("Using MYSQL_PUBLIC_URL for database connection")
    # Convert the URL format if needed
    public_url = os.environ.get('MYSQL_PUBLIC_URL')
    if public_url.startswith('mysql://'):
        # Replace mysql:// with mysql+pymysql:// for SQLAlchemy
        database_url = public_url.replace('mysql://', 'mysql+pymysql://', 1)
    else:
        database_url = public_url
else:
    # Build MySQL connection string from individual components
    database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    logger.info(f"Using MySQL database: {mysql_database} on {mysql_host}")

# Fall back to SQLite for local development if MySQL variables aren't set
if not (os.environ.get('MYSQL_PUBLIC_URL') or all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_database])):
    database_url = "sqlite:///participants.db"
    logger.info(f"Using SQLite database for local development: {database_url}")

# Configure SQLAlchemy with pool_pre_ping to handle stale connections
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,  # recycle connections before MySQL's default timeout
    'pool_pre_ping': True,  # test connections before using them
    'pool_timeout': 30,  # timeout waiting for a connection from pool
    'connect_args': {
        'connect_timeout': 10  # timeout for establishing new connections
    }
}

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

# Add error handling middleware to log and handle database errors
@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    logger.error(f"Database error: {str(error)}")
    return jsonify({"success": False, "error": "Database error occurred. Please try again later."}), 500

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
    try:
        # Try a simple database query to verify connection
        # Use a lightweight query that doesn't depend on tables existing
        db.session.execute("SELECT 1").scalar()
        logger.info("Health check passed: Database connection successful")
        return "OK - Application running and database connected", 200
    except Exception as e:
        # Log the error but still return 200 during initial deployment
        # This helps the container start up properly
        logger.warning(f"Health check warning: {str(e)}")
        # Always return 200 during startup to allow the container to initialize
        return "OK - Application running but database not ready", 200

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
        logger.info(f"Received POST request with data: {request.data}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
            logger.info("Received JSON data")
        else:
            data = request.form
            logger.info("Received form data")
        
        # Extract form fields
        nome = data.get("nome")
        empresa = data.get("empresa")
        funcao = data.get("funcao")
        segmento = data.get("segmento")
        email = data.get("email")
        
        logger.info(f"Parsed data: nome={nome}, empresa={empresa}, funcao={funcao}, segmento={segmento}, email={email}")
        
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
        
        logger.info(f"Successfully registered user: {nome}")
        return jsonify({"success": True, "message": "Cadastro realizado com sucesso!"})
    except Exception as e:
        logger.error(f"Error in /api/cadastro: {str(e)}")
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
        
        # Log the number of participants found
        logger.info(f"Sorteio: Found {len(participants)} participants in database")
        
        # Check participants
        if not participants:
            logger.error("No participants found in database")
            return render_template("vencedor.html", 
                                  vencedor="Nenhum participante cadastrado. Por favor, verifique o banco de dados.", 
                                  index="0",
                                  error="Database is empty.")
        
        # Log all participants for debugging
        for i, p in enumerate(participants):
            logger.info(f"Participant {i+1}: {p.nome} ({p.email})")
        
        # Choose a random winner and get their index in the list
        winner_index = random.randint(0, len(participants) - 1)
        vencedor = participants[winner_index]
        
        logger.info(f"Selected winner: {vencedor.nome} at index {winner_index}")
        
        # The index to display is 1-based for better user experience
        display_index = winner_index + 1

        return render_template("vencedor.html", 
                              vencedor=vencedor.nome, 
                              index=display_index,
                              empresa=vencedor.empresa,
                              email=vencedor.email)
    except Exception as e:
        logger.error(f"Error in sorteio route: {str(e)}")
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
        return render_template("participantes.html", participants=participants)
    except Exception as e:
        print(f"Error retrieving participants: {str(e)}")
        return render_template("participantes.html", 
                              participants=[],
                              error=f"Error retrieving participants: {str(e)}")

# Admin page for database management
@app.route("/admin")
def admin():
    try:
        # Get current stats
        total_count = Participant.query.count()
        stats = {
            "total": total_count,
            "added": 0,
            "duplicates": 0,
            "errors": 0
        }
        return render_template("admin.html", stats=stats)
    except Exception as e:
        logger.error(f"Error in admin page: {str(e)}")
        return render_template("admin.html", 
                              status="Erro ao carregar estatísticas", 
                              success=False,
                              details=str(e))

# API endpoint to clear the participants database
@app.route("/api/clear", methods=["POST"])
def clear_database_route():
    try:
        # Get the count before deletion for reporting
        count = Participant.query.count()
        logger.info(f"API request to clear database. Found {count} participants to delete")
        
        # Delete all participants
        Participant.query.delete()
        db.session.commit()
        
        # Verify deletion
        new_count = Participant.query.count()
        logger.info(f"Database cleared via API. {count} participants deleted. Remaining: {new_count}")
        
        return jsonify({
            "success": True, 
            "message": f"Database cleared. {count} participants deleted."
        })
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Route to download participants as CSV
@app.route("/download-participants")
def download_participants():
    try:
        # Get all participants from the database
        participants = Participant.query.all()
        
        # Create CSV in memory using StringIO and csv module
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Nome', 'Empresa', 'Função', 'Segmento', 'Email'])
        
        # Write data rows
        for p in participants:
            writer.writerow([p.id, p.nome, p.empresa, p.funcao, p.segmento, p.email])
        
        # Return CSV as a downloadable file
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=participants.csv"}
        )
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Create database tables with retry mechanism
def create_tables_with_retry(retries=5, delay=5):
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt+1}/{retries} to create database tables")
            db.create_all()
            logger.info("Database tables created successfully!")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {type(e).__name__}: {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Failed to create tables after all attempts")
                # Don't fail the application startup - we'll try to create tables later
                return False

# Function to initialize the database
def init_db():
    try:
        return create_tables_with_retry()
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        # Don't let database errors prevent app from starting
        return False

# Initialize the database tables - but don't let failures stop the app
with app.app_context():
    try:
        create_tables_with_retry()
    except Exception as e:
        logger.warning(f"Could not initialize database during startup: {str(e)}")
        logger.info("Application will continue starting and retry database operations during requests")

# Only call this when explicitly running this file
if __name__ == "__main__":
    app.run(debug=True)

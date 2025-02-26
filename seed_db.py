import json
import os
import logging
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    """
    Seed the database with participants from code.txt
    Returns True if successful, False otherwise
    """
    # Import here to avoid circular imports
    from app import db, Participant
    
    try:
        # Path to the code.txt file
        code_file_path = os.path.join(os.path.dirname(__file__), 'code.txt')
        
        # Check if the file exists
        if not os.path.exists(code_file_path):
            logger.error(f"File not found: {code_file_path}")
            return False
        
        # Read the JSON data from code.txt
        with open(code_file_path, 'r', encoding='utf-8') as file:
            participants_data = json.load(file)
        
        logger.info(f"Loaded {len(participants_data)} participants from code.txt")
        
        # Count of successfully added participants
        success_count = 0
        duplicate_count = 0
        error_count = 0
        
        # Insert each participant into the database
        for participant_data in participants_data:
            try:
                # Check if participant with this email already exists
                existing = Participant.query.filter_by(email=participant_data['email']).first()
                
                if existing:
                    logger.info(f"Participant with email {participant_data['email']} already exists, skipping")
                    duplicate_count += 1
                    continue
                
                # Create new participant
                new_participant = Participant(
                    nome=participant_data['nome'],
                    empresa=participant_data['empresa'],
                    funcao=participant_data['funcao'],
                    segmento=participant_data['segmento'],
                    email=participant_data['email']
                )
                
                # Add to database
                db.session.add(new_participant)
                db.session.commit()
                success_count += 1
                logger.info(f"Added participant: {participant_data['nome']}")
                
            except IntegrityError:
                # Handle duplicate emails
                db.session.rollback()
                logger.warning(f"Duplicate email: {participant_data['email']}")
                duplicate_count += 1
            except Exception as e:
                # Handle other errors
                db.session.rollback()
                logger.error(f"Error adding participant {participant_data.get('nome', 'unknown')}: {str(e)}")
                error_count += 1
        
        # Log summary
        logger.info(f"Seeding complete: {success_count} added, {duplicate_count} duplicates, {error_count} errors")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        return False

# Run the seed function if this script is executed directly
if __name__ == "__main__":
    # Import here to avoid circular imports
    from app import app
    
    # Always use SQLite for local development when running directly
    logger.info("Using SQLite for local development")
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///participants.db"
    
    # Recreate tables for SQLite
    with app.app_context():
        from app import db
        logger.info("Creating database tables")
        db.create_all()
        logger.info("Tables created successfully")
    
    # Seed the database
    with app.app_context():
        success = seed_database()
        if success:
            print("Database seeded successfully!")
            # Print count of participants
            from app import Participant
            count = Participant.query.count()
            print(f"Total participants in database: {count}")
        else:
            print("Failed to seed database. Check logs for details.") 
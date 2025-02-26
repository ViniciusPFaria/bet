import json
import os
from app import app, db, Participant
import sys

def seed_database():
    """
    Seeds the database with initial data from code.txt
    """
    print("Starting database seeding process...")
    
    # Get the path to the code.txt file
    seed_file_path = os.path.join(os.path.dirname(__file__), 'code.txt')
    
    try:
        # Check if the file exists
        if not os.path.exists(seed_file_path):
            print(f"Error: Seed file not found at {seed_file_path}")
            return False
        
        # Read the JSON data from the file
        with open(seed_file_path, 'r', encoding='utf-8') as file:
            seed_data = json.load(file)
        
        print(f"Loaded {len(seed_data)} records from seed file")
        
        # Check if there is already data in the database
        existing_count = Participant.query.count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} records. Skipping seeding.")
            return True
        
        # Insert each record into the database
        added_count = 0
        skipped_count = 0
        
        for record in seed_data:
            # Check if this email already exists
            existing = Participant.query.filter_by(email=record['email']).first()
            
            if existing:
                print(f"Skipping duplicate email: {record['email']}")
                skipped_count += 1
                continue
                
            try:
                # Create a new participant record
                participant = Participant(
                    nome=record['nome'],
                    empresa=record['empresa'],
                    funcao=record['funcao'],
                    segmento=record['segmento'],
                    email=record['email']
                )
                
                # Add to the session
                db.session.add(participant)
                added_count += 1
                
            except Exception as e:
                print(f"Error adding record {record['nome']}: {str(e)}")
                skipped_count += 1
        
        # Commit all changes
        db.session.commit()
        print(f"Database seeding complete. Added {added_count} records, skipped {skipped_count} records.")
        return True
        
    except Exception as e:
        print(f"Error during database seeding: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Run the seeding function within the app context
    with app.app_context():
        success = seed_database()
        if not success:
            sys.exit(1) 
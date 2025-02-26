import json
import os
from app import app, db, Participant
import sys
import traceback

def seed_database():
    """
    Seeds the database with initial data from code.txt
    """
    print("Starting database seeding process...")
    
    # Get the path to the code.txt file
    seed_file_path = os.path.join(os.path.dirname(__file__), 'code.txt')
    print(f"Looking for seed file at: {seed_file_path}")
    
    try:
        # Check if the file exists
        if not os.path.exists(seed_file_path):
            print(f"Error: Seed file not found at {seed_file_path}")
            return False
        
        print(f"Seed file found, attempting to read JSON data...")
        # Read the JSON data from the file
        try:
            with open(seed_file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
                print(f"File content length: {len(file_content)} characters")
                seed_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"First 200 characters of file: {file_content[:200]}")
            return False
        
        print(f"Successfully loaded {len(seed_data)} records from seed file")
        
        # Check if there is already data in the database
        existing_count = Participant.query.count()
        print(f"Current database has {existing_count} existing records")
        
        if existing_count > 0:
            print(f"Database already contains {existing_count} records. Checking if we should update...")
            
            # Let's always proceed with seeding, but skip duplicates
            print("Proceeding with seeding to ensure all entries from code.txt exist")
        
        # Insert each record into the database
        added_count = 0
        skipped_count = 0
        
        for i, record in enumerate(seed_data):
            try:
                print(f"Processing record {i+1}/{len(seed_data)}: {record.get('nome', 'Unknown')}")
                
                # Check if required fields exist
                if not all(k in record for k in ['nome', 'empresa', 'funcao', 'segmento', 'email']):
                    missing = [k for k in ['nome', 'empresa', 'funcao', 'segmento', 'email'] if k not in record]
                    print(f"Skipping record {i+1} - Missing required fields: {missing}")
                    skipped_count += 1
                    continue
                
                # Check if this email already exists
                existing = Participant.query.filter_by(email=record['email']).first()
                
                if existing:
                    print(f"Skipping duplicate email: {record['email']}")
                    skipped_count += 1
                    continue
                    
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
                
                # Commit every 10 records to avoid large transactions
                if added_count % 10 == 0:
                    print(f"Committing batch of 10 records...")
                    db.session.commit()
                
            except Exception as e:
                print(f"Error adding record {i+1} ({record.get('nome', 'Unknown')}): {str(e)}")
                traceback.print_exc()
                skipped_count += 1
        
        # Commit any remaining changes
        if added_count % 10 != 0:
            print(f"Committing final batch of records...")
            db.session.commit()
            
        print(f"Database seeding complete. Added {added_count} records, skipped {skipped_count} records.")
        
        # Verify seeding was successful
        final_count = Participant.query.count()
        print(f"Final database record count: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"Error during database seeding: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Run the seeding function within the app context
    with app.app_context():
        success = seed_database()
        if not success:
            sys.exit(1) 
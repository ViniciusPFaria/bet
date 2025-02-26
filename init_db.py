from app import app, db, init_db
import sys
from seed_db import seed_database
import os

print("Initializing database...")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory:")
for file in os.listdir('.'):
    print(f"  - {file}")

try:
    # Initialize the database
    init_db()
    print("Database initialization complete!")
    
    # Seed the database with initial data
    print("Seeding database with initial data...")
    with app.app_context():
        success = seed_database()
        if not success:
            print("WARNING: Database seeding failed!")
        else:
            print("Database seeding completed successfully!")
    
except Exception as e:
    print(f"ERROR: Failed to initialize database: {str(e)}")
    
    # Don't exit with an error for Railway deployment
    # This allows the application to still start even if 
    # the initial DB creation fails
    print("Continuing with application startup anyway...")
    # sys.exit(1)  # Uncomment this if you want to fail on DB init error 
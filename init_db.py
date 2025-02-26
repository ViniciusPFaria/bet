from app import app, db, init_db
import sys

print("Initializing database...")

try:
    init_db()
    print("Database initialization complete!")
except Exception as e:
    print(f"ERROR: Failed to initialize database: {str(e)}")
    
    # Don't exit with an error for Railway deployment
    # This allows the application to still start even if 
    # the initial DB creation fails
    print("Continuing with application startup anyway...")
    # sys.exit(1)  # Uncomment this if you want to fail on DB init error 
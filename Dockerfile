FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a script to initialize the database and start the application
RUN echo '#!/bin/bash \n\
echo "Checking database connection..." \n\
python -c "from app import app, db; \n\
import time; \n\
for i in range(5): \n\
    try: \n\
        with app.app_context(): \n\
            db.create_all(); \n\
            print(\"Database connected and tables created.\"); \n\
            break; \n\
    except Exception as e: \n\
        print(f\"Attempt {i+1}/5: {str(e)}\"); \n\
        if i < 4: \n\
            print(\"Retrying in 5 seconds...\"); \n\
            time.sleep(5); \n\
        else: \n\
            print(\"Failed to connect to database after 5 attempts.\"); \n\
" \n\
\n\
# Start Gunicorn \n\
echo "Starting application..." \n\
exec gunicorn --bind 0.0.0.0:$PORT app:app \n\
' > /app/startup.sh

RUN chmod +x /app/startup.sh

# Expose port (Railway sets $PORT env variable)
EXPOSE 8000

# Command to run the application
CMD ["./startup.sh"] 
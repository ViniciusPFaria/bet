FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a script to initialize the database and start the application
RUN echo '#!/bin/bash \n\
echo "Initializing database..." \n\
python init_db.py \n\
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
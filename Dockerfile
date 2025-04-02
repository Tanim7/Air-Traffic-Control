# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY server.py .
COPY radar.py .
COPY frontend.html .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

# Use official Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=3430

# Set work directory
WORKDIR /app

# Install system packages (eventlet dependencies)
RUN apt-get update && apt-get install -y build-essential

# Copy app files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the desired port
EXPOSE 3430

# Run the app using Gunicorn and Eventlet
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:3430", "app:app"]

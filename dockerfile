# Stage 1: Base build stage
FROM python:3.9-slim

 
# Set the working directory
WORKDIR /rwagproject

# Install system dependencies, including pkg-config
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
# Copy the requirements file first (better caching)
COPY requirements.txt /rwagproject/
 
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gettext for Django translations
RUN apt-get update && apt-get install -y gettext

COPY . /rwagproject

# Expose the application port
EXPOSE 8000 
 
# Start the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "rwagproject.wsgi:application"]

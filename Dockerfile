# Use Alpine Linux for small image size
FROM python:3.9-alpine

# Install system dependencies
RUN apk add --no-cache git gcc python3-dev musl-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create app directory
WORKDIR /app

# Copy application files
COPY src/ /app/src/
COPY config/ /app/config/

# Set environment variables
ENV CONFIG_PATH=/app/config/config.yaml
ENV PYTHONPATH=/app

# Run the scheduler
CMD ["python", "/app/src/scheduler.py"]
# Use Alpine Linux for small image size
FROM python:3.9-alpine

# Install dependencies
RUN apk add --no-cache git

# Create app directory first
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL files
COPY . .

# Set environment variables
ENV CONFIG_PATH=/app/config/config.yaml
ENV PYTHONPATH=/app

# Directly run the script (most reliable method)
CMD ["python", "/app/src/scheduler.py"]
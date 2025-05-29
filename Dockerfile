# set version label
ARG BUILD_DATE
ARG VERSION
FROM python:3.9-alpine
#FROM python:3.9-slim
LABEL build_version="Build-version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="danutzzzzz"

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

# Create log directory and set permissions
RUN mkdir -p /app/config/logs && chmod 777 /app/config/logs

# Add volume for log persistence (optional)
VOLUME /app/config/logs

# Set environment variables
ENV CONFIG_PATH=/app/config/config.yaml
ENV PYTHONPATH=/app

# Run the scheduler
CMD ["python", "/app/src/scheduler.py"]
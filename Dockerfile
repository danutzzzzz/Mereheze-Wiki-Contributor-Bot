# Use Alpine Linux for small image size
FROM python:3.9-alpine

# Install system dependencies
echo "**** Install system dependencies ****" && \
RUN apk add --no-cache git gcc python3-dev musl-dev

# Install Python dependencies
echo "**** Install Python dependencies ****" && \
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create app directory
echo "**** Install Python dependencies ****" && \
WORKDIR /app

# Copy application files
echo "**** Copy application files ****" && \
COPY src/ /app/src/
COPY config/ /app/config/

# Create log directory and set permissions
echo "**** set permissions ****" && \
RUN mkdir -p /app/config/logs && chmod 777 /app/config/logs

# Add volume for log persistence (optional)
VOLUME /app/config/logs

# Set environment variables
echo "**** Set environment variables ****" && \
ENV CONFIG_PATH=/app/config/config.yaml
ENV PYTHONPATH=/app

# Run the scheduler
printf "version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
echo "**** Run the scheduler ****" && \
CMD ["python", "/app/src/scheduler.py"]
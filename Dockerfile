# Use Alpine Linux for small image size
FROM python:3.9-alpine

# Install system dependencies
RUN echo "**** Install system dependencies ****" && \
RUN apk add --no-cache git gcc python3-dev musl-dev

# Install Python dependencies
RUN echo "**** Install Python dependencies ****" && \
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create app directory
RUN echo "**** Install Python dependencies ****" && \
WORKDIR /app

# Copy application files
RUN echo "**** Copy application files ****" && \
COPY src/ /app/src/
COPY config/ /app/config/

# Create log directory and set permissions
RUN echo "**** set permissions ****" && \
RUN mkdir -p /app/config/logs && chmod 777 /app/config/logs

# Add volume for log persistence (optional)
VOLUME /app/config/logs

# Set environment variables
RUN echo "**** Set environment variables ****" && \
ENV CONFIG_PATH=/app/config/config.yaml
ENV PYTHONPATH=/app

# Run the scheduler
RUN printf "version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
RUN echo "**** Run the scheduler ****" && \
CMD ["python", "/app/src/scheduler.py"]
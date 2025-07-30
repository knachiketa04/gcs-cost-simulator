#!/bin/bash

# Local Docker test script
# Tests the app locally before deploying to Cloud Run

set -e

SERVICE_NAME="gcs-cost-simulator"
LOCAL_PORT="8080"

echo "🧪 Testing GCS Cost Simulator locally with Docker..."
echo "================================================"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ ERROR: Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

# Build the image
echo "🏗️  Building Docker image..."
docker build -t $SERVICE_NAME:local .

# Stop any existing container
echo "🧹 Cleaning up existing containers..."
docker stop $SERVICE_NAME 2>/dev/null || true
docker rm $SERVICE_NAME 2>/dev/null || true

# Run the container
echo "🚀 Starting container on port $LOCAL_PORT..."
docker run -d \
    --name $SERVICE_NAME \
    -p $LOCAL_PORT:8080 \
    -e PORT=8080 \
    $SERVICE_NAME:local

# Wait a moment for startup
echo "⏳ Waiting for app to start..."
sleep 5

# Check if container is running
if docker ps | grep -q $SERVICE_NAME; then
    echo "✅ Container is running!"
    echo ""
    echo "🌐 Open your browser and go to:"
    echo "   http://localhost:$LOCAL_PORT"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker logs $SERVICE_NAME -f"
    echo "   Stop app:  docker stop $SERVICE_NAME"
    echo "   Remove:    docker rm $SERVICE_NAME"
    echo ""
    echo "🔍 Testing the app now..."
    
    # Wait for the app to be ready
    for i in {1..30}; do
        if curl -s http://localhost:$LOCAL_PORT > /dev/null 2>&1; then
            echo "✅ App is responding at http://localhost:$LOCAL_PORT"
            echo ""
            echo "🎉 Local test successful! Ready for Cloud Run deployment."
            break
        else
            echo "⏳ Waiting for app to respond... ($i/30)"
            sleep 2
        fi
    done
    
    if [ $i -eq 30 ]; then
        echo "❌ App is not responding after 60 seconds"
        echo "📋 Check logs: docker logs $SERVICE_NAME"
    fi
else
    echo "❌ Container failed to start"
    echo "📋 Check logs: docker logs $SERVICE_NAME"
    exit 1
fi

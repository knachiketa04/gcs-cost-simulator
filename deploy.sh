#!/bin/bash

# GCS Cost Simulator - Cloud Run Deployment Script
# This script deploys the app to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=""
REGION="us-central1"  # Cheapest region with low CO2
SERVICE_NAME="gcs-cost-simulator"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GCS Cost Simulator - Cloud Run Deployment${NC}"
echo "================================================"

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ ERROR: PROJECT_ID is not set in this script${NC}"
    echo -e "${YELLOW}Please edit deploy.sh and set your Google Cloud PROJECT_ID${NC}"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ ERROR: gcloud CLI is not installed${NC}"
    echo -e "${YELLOW}Please install Google Cloud CLI: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker is not running${NC}"
    echo -e "${YELLOW}Please start Docker Desktop${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo ""

# Authenticate with Google Cloud (if needed)
echo -e "${BLUE}🔐 Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with Google Cloud${NC}"
    echo -e "${BLUE}Opening browser for authentication...${NC}"
    gcloud auth login
fi

# Set the project
echo -e "${BLUE}📝 Setting Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Build the Docker image
echo -e "${BLUE}🏗️  Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Push the image to Google Container Registry
echo -e "${BLUE}📤 Pushing image to Google Container Registry...${NC}"
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 80 \
    --timeout 300 \
    --max-instances 10 \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "================================================"
echo -e "${GREEN}🌐 Your app is live at:${NC}"
echo -e "${BLUE}$SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}📊 Monitor your app:${NC}"
echo "  Cloud Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/overview?project=$PROJECT_ID"
echo "  Logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50 --format json"
echo ""
echo -e "${YELLOW}💰 Cost monitoring:${NC}"
echo "  Your app will scale to zero when not in use"
echo "  First 240K vCPU-seconds and 450K GiB-seconds are FREE per month"
echo "  Monitor costs: https://console.cloud.google.com/billing"
echo ""
echo -e "${GREEN}🎉 Happy simulating!${NC}"

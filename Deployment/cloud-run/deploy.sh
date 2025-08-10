#!/bin/bash

# Google Cloud Run Deployment Script for Micro-Agent Platform
# Optimized for serverless deployment with external services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-micro-agent-api}"
IMAGE_NAME="${IMAGE_NAME:-micro-agent-platform}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
MIN_INSTANCES="${MIN_INSTANCES:-1}"
MAX_INSTANCES="${MAX_INSTANCES:-100}"
CPU="${CPU:-2}"
MEMORY="${MEMORY:-2Gi}"
TIMEOUT="${TIMEOUT:-300s}"
CONCURRENCY="${CONCURRENCY:-80}"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install Google Cloud SDK first."
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        print_error "Not authenticated with Google Cloud. Run: gcloud auth login"
        exit 1
    fi
    
    # Check project ID
    if [[ "$PROJECT_ID" == "your-project-id" ]]; then
        print_error "Please set PROJECT_ID environment variable or update GOOGLE_CLOUD_PROJECT"
        exit 1
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    print_status "Enabling required Google Cloud APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable redis.googleapis.com
    
    print_success "Prerequisites checked."
}

create_secrets() {
    print_status "Creating secrets in Secret Manager..."
    
    # Create secrets (you'll need to add the actual values)
    secrets=(
        "api-key:your-secure-api-key-here-change-in-production"
        "flask-secret-key:your-super-secret-flask-key-here-minimum-32-characters"
        "gemini-api-key:your-gemini-api-key-here"
        "openai-api-key:your-openai-api-key-here"
        "anthropic-api-key:your-anthropic-api-key-here"
        "redis-password:your-secure-redis-password-here"
    )
    
    for secret_pair in "${secrets[@]}"; do
        secret_name="${secret_pair%:*}"
        secret_value="${secret_pair#*:}"
        
        # Check if secret exists
        if gcloud secrets describe "$secret_name" &>/dev/null; then
            print_status "Secret $secret_name already exists, skipping..."
        else
            print_status "Creating secret: $secret_name"
            echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
        fi
    done
    
    print_warning "Please update the secrets with actual values using:"
    print_warning "gcloud secrets versions add SECRET_NAME --data-file=secret_file.txt"
    
    print_success "Secrets created in Secret Manager."
}

create_redis_instance() {
    print_status "Creating Redis instance (Memorystore)..."
    
    REDIS_INSTANCE_NAME="micro-agent-redis"
    
    # Check if Redis instance exists
    if gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" &>/dev/null; then
        print_status "Redis instance already exists."
    else
        print_status "Creating new Redis instance..."
        gcloud redis instances create "$REDIS_INSTANCE_NAME" \
            --size=1 \
            --region="$REGION" \
            --redis-version=redis_7_0 \
            --auth-enabled \
            --tier=basic
        
        print_status "Waiting for Redis instance to be ready..."
        gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" --format="value(state)" | grep -q "READY"
    fi
    
    # Get Redis connection details
    REDIS_HOST=$(gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" --format="value(host)")
    REDIS_PORT=$(gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" --format="value(port)")
    
    print_success "Redis instance ready at $REDIS_HOST:$REDIS_PORT"
}

build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    IMAGE_URL="gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    
    # Build using Cloud Build for optimization
    print_status "Building image with Cloud Build..."
    gcloud builds submit --tag "$IMAGE_URL" --file="cloud-run/Dockerfile.cloudrun" .
    
    print_success "Image built and pushed: $IMAGE_URL"
}

deploy_service() {
    print_status "Deploying Cloud Run service..."
    
    IMAGE_URL="gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    
    # Deploy Cloud Run service
    gcloud run deploy "$SERVICE_NAME" \
        --image="$IMAGE_URL" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --min-instances="$MIN_INSTANCES" \
        --max-instances="$MAX_INSTANCES" \
        --cpu="$CPU" \
        --memory="$MEMORY" \
        --timeout="$TIMEOUT" \
        --concurrency="$CONCURRENCY" \
        --execution-environment=gen2 \
        --cpu-boost \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT" \
        --set-secrets="API_KEY=api-key:latest,FLASK_SECRET_KEY=flask-secret-key:latest,GEMINI_API_KEY=gemini-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,REDIS_PASSWORD=redis-password:latest"
    
    print_success "Cloud Run service deployed."
}

setup_monitoring() {
    print_status "Setting up Cloud Monitoring..."
    
    # Enable Cloud Monitoring API
    gcloud services enable monitoring.googleapis.com
    
    # Create uptime check
    print_status "Creating uptime check for health endpoint..."
    
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)")
    
    cat > /tmp/uptime-check.json <<EOF
{
  "displayName": "Micro-Agent API Health Check",
  "httpCheck": {
    "path": "/api/v1/health",
    "port": 443,
    "useSsl": true
  },
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "$PROJECT_ID",
      "host": "$(echo $SERVICE_URL | sed 's|https://||' | sed 's|/.*||')"
    }
  },
  "timeout": "10s",
  "period": "60s"
}
EOF
    
    # Apply uptime check (requires gcloud alpha)
    gcloud alpha monitoring uptime create-config /tmp/uptime-check.json || print_warning "Could not create uptime check (requires alpha component)"
    
    rm /tmp/uptime-check.json
    
    print_success "Monitoring configured."
}

show_deployment_info() {
    print_status "Getting deployment information..."
    
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)")
    
    echo
    print_success "=== DEPLOYMENT COMPLETED ==="
    echo -e "🚀 ${GREEN}Service URL:${NC} $SERVICE_URL"
    echo -e "❤️  ${GREEN}Health Check:${NC} $SERVICE_URL/api/v1/health"
    echo -e "📊 ${GREEN}Status:${NC} $SERVICE_URL/api/v1/status"
    echo -e "📈 ${GREEN}Metrics:${NC} $SERVICE_URL/api/v1/metrics"
    echo
    echo -e "🔧 ${GREEN}Management Commands:${NC}"
    echo -e "   View logs: gcloud run services logs read $SERVICE_NAME --platform=managed --region=$REGION"
    echo -e "   Update service: gcloud run services update $SERVICE_NAME --platform=managed --region=$REGION"
    echo -e "   Delete service: gcloud run services delete $SERVICE_NAME --platform=managed --region=$REGION"
    echo
    echo -e "📊 ${GREEN}Monitoring:${NC}"
    echo -e "   Cloud Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
    echo -e "   Metrics: https://console.cloud.google.com/monitoring"
    echo -e "   Logs: https://console.cloud.google.com/logs/query;query=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22$SERVICE_NAME%22"
    echo
    
    # Test the deployment
    print_status "Testing deployment..."
    if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/v1/health" | grep -q "200"; then
        print_success "✅ Health check passed!"
    else
        print_warning "⚠️ Health check failed. Check logs for issues."
    fi
}

cleanup_deployment() {
    print_status "Cleaning up Cloud Run deployment..."
    
    # Delete Cloud Run service
    gcloud run services delete "$SERVICE_NAME" --platform=managed --region="$REGION" --quiet
    
    # Delete Redis instance (optional - comment out if you want to keep data)
    print_warning "Do you want to delete the Redis instance? This will delete all cached data."
    read -p "Delete Redis instance? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        gcloud redis instances delete "micro-agent-redis" --region="$REGION" --quiet
    fi
    
    # Delete secrets (optional)
    print_warning "Do you want to delete secrets from Secret Manager?"
    read -p "Delete secrets? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        secrets=("api-key" "flask-secret-key" "gemini-api-key" "openai-api-key" "anthropic-api-key" "redis-password")
        for secret in "${secrets[@]}"; do
            gcloud secrets delete "$secret" --quiet || true
        done
    fi
    
    print_success "Cleanup completed."
}

show_help() {
    echo "Google Cloud Run Deployment Script for Micro-Agent Platform"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy      Full deployment (default)"
    echo "  status      Show deployment status"
    echo "  cleanup     Remove all resources"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PROJECT_ID    Google Cloud Project ID (required)"
    echo "  REGION        Deployment region (default: us-central1)"
    echo "  SERVICE_NAME  Cloud Run service name (default: micro-agent-api)"
    echo "  IMAGE_TAG     Container image tag (default: latest)"
    echo "  MIN_INSTANCES Minimum instances (default: 1)"
    echo "  MAX_INSTANCES Maximum instances (default: 100)"
    echo "  CPU           CPU allocation (default: 2)"
    echo "  MEMORY        Memory allocation (default: 2Gi)"
    echo ""
    echo "Examples:"
    echo "  PROJECT_ID=my-project $0 deploy"
    echo "  PROJECT_ID=my-project REGION=us-west1 $0 deploy"
    echo "  $0 status"
    echo "  $0 cleanup"
    echo ""
}

# Main deployment function
full_deploy() {
    print_status "Starting Cloud Run deployment of Micro-Agent Platform..."
    
    check_prerequisites
    create_secrets
    create_redis_instance
    build_and_push_image
    deploy_service
    setup_monitoring
    show_deployment_info
    
    print_success "🎉 Cloud Run deployment completed successfully!"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        full_deploy
        ;;
    "status")
        show_deployment_info
        ;;
    "cleanup")
        cleanup_deployment
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
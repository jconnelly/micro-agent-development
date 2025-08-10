#!/bin/bash

# Micro-Agent Development Platform - Deployment Script
# Supports development, staging, and production deployments

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_NAME="micro-agent-platform"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

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

check_requirements() {
    print_status "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file ($ENV_FILE) not found."
        if [ -f ".env.example" ]; then
            print_status "Copying .env.example to $ENV_FILE..."
            cp .env.example "$ENV_FILE"
            print_warning "Please configure $ENV_FILE with your actual values before proceeding."
            exit 1
        else
            print_error "Neither $ENV_FILE nor .env.example found."
            exit 1
        fi
    fi
    
    print_success "All requirements satisfied."
}

build_images() {
    print_status "Building Docker images..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    fi
    
    print_success "Docker images built successfully."
}

deploy_development() {
    print_status "Deploying development environment..."
    
    # Use development compose file
    DOCKER_COMPOSE_FILE="docker-compose.dev.yml"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi
    
    print_success "Development environment deployed successfully!"
    print_status "API available at: http://localhost:5000"
    print_status "API Health Check: http://localhost:5000/api/v1/health"
    print_status "API Status: http://localhost:5000/api/v1/status"
}

deploy_production() {
    print_status "Deploying production environment..."
    
    # Build images first
    build_images
    
    # Deploy with production compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi
    
    # Wait for health check
    print_status "Waiting for application to be ready..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        print_success "Production environment deployed successfully!"
        print_status "API available at: http://localhost:8000"
        print_status "API Health Check: http://localhost:8000/api/v1/health"
        print_status "API Status: http://localhost:8000/api/v1/status"
    else
        print_error "Deployment may have failed. Please check logs."
        show_logs
        exit 1
    fi
}

deploy_with_monitoring() {
    print_status "Deploying with full monitoring stack..."
    
    # Build images
    build_images
    
    # Deploy with monitoring profile
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" --profile full up -d
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" --profile full up -d
    fi
    
    print_success "Full stack deployed successfully!"
    print_status "API: http://localhost:8000"
    print_status "Prometheus: http://localhost:9090"
    print_status "Grafana: http://localhost:3000 (admin/admin)"
}

show_status() {
    print_status "Current deployment status:"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" ps
    fi
}

show_logs() {
    print_status "Showing application logs:"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f --tail=100 micro-agent-api
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" logs -f --tail=100 micro-agent-api
    fi
}

stop_deployment() {
    print_status "Stopping deployment..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" down
    fi
    
    print_success "Deployment stopped."
}

cleanup_deployment() {
    print_status "Cleaning up deployment (removing volumes)..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v --remove-orphans
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" down -v --remove-orphans
    fi
    
    # Remove unused images
    docker image prune -f
    
    print_success "Cleanup completed."
}

show_help() {
    echo "Micro-Agent Development Platform - Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Deploy development environment (port 5000)"
    echo "  prod        Deploy production environment (port 8000)"
    echo "  monitoring  Deploy with full monitoring stack"
    echo "  build       Build Docker images"
    echo "  status      Show current deployment status"
    echo "  logs        Show application logs"
    echo "  stop        Stop current deployment"
    echo "  cleanup     Stop deployment and remove volumes"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev          # Start development environment"
    echo "  $0 prod         # Start production environment"
    echo "  $0 monitoring   # Start with Prometheus + Grafana"
    echo "  $0 logs         # View application logs"
    echo ""
}

# Main script logic
case "${1:-help}" in
    "dev"|"development")
        check_requirements
        deploy_development
        ;;
    "prod"|"production")
        check_requirements
        deploy_production
        ;;
    "monitoring"|"full")
        check_requirements
        deploy_with_monitoring
        ;;
    "build")
        check_requirements
        build_images
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_deployment
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
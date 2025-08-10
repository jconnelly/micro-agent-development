#!/bin/bash

# Kubernetes Deployment Script for Micro-Agent Platform
# Supports development, staging, and production environments

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="micro-agent-platform"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-your-registry.com}"
PROJECT_NAME="${PROJECT_NAME:-micro-agent-platform}"

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
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check if metrics-server is available (required for HPA)
    if ! kubectl get apiservice v1beta1.metrics.k8s.io &> /dev/null; then
        print_warning "Metrics server not found. HPA may not work properly."
        print_status "Install metrics-server: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    fi
    
    print_success "Prerequisites check completed."
}

create_namespace() {
    print_status "Creating namespace..."
    kubectl apply -f "${SCRIPT_DIR}/namespace.yaml"
    print_success "Namespace created/updated."
}

deploy_secrets() {
    print_status "Deploying secrets..."
    
    # Check if secrets file exists
    if [ ! -f "${SCRIPT_DIR}/secret.yaml" ]; then
        print_error "secret.yaml not found. Please create secrets configuration."
        exit 1
    fi
    
    print_warning "Please ensure you have updated the secret.yaml file with actual values!"
    read -p "Have you updated the secrets with real values? (y/N): " confirm
    if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
        print_error "Please update secret.yaml with actual API keys and passwords before deploying."
        exit 1
    fi
    
    kubectl apply -f "${SCRIPT_DIR}/secret.yaml"
    print_success "Secrets deployed."
}

deploy_configmaps() {
    print_status "Deploying configuration..."
    kubectl apply -f "${SCRIPT_DIR}/configmap.yaml"
    print_success "ConfigMaps deployed."
}

deploy_rbac() {
    print_status "Deploying RBAC..."
    kubectl apply -f "${SCRIPT_DIR}/rbac.yaml"
    print_success "RBAC configured."
}

deploy_storage() {
    print_status "Deploying persistent storage..."
    
    # Check if storage classes exist
    print_status "Available storage classes:"
    kubectl get storageclass
    
    kubectl apply -f "${SCRIPT_DIR}/pvc.yaml"
    
    # Wait for PVCs to be bound
    print_status "Waiting for persistent volumes to be bound..."
    kubectl wait --for=condition=Bound pvc/redis-pvc -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=Bound pvc/prometheus-pvc -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=Bound pvc/grafana-pvc -n ${NAMESPACE} --timeout=300s
    
    print_success "Storage deployed and bound."
}

deploy_applications() {
    print_status "Deploying applications..."
    
    # Update image tags in deployment
    if [[ "${IMAGE_TAG}" != "latest" ]]; then
        print_status "Using image tag: ${IMAGE_TAG}"
        sed -i.bak "s|micro-agent-platform:latest|${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}|g" "${SCRIPT_DIR}/deployment.yaml"
    fi
    
    kubectl apply -f "${SCRIPT_DIR}/deployment.yaml"
    kubectl apply -f "${SCRIPT_DIR}/monitoring.yaml"
    
    # Restore original deployment file if we modified it
    if [[ -f "${SCRIPT_DIR}/deployment.yaml.bak" ]]; then
        mv "${SCRIPT_DIR}/deployment.yaml.bak" "${SCRIPT_DIR}/deployment.yaml"
    fi
    
    print_success "Applications deployed."
}

deploy_services() {
    print_status "Deploying services..."
    kubectl apply -f "${SCRIPT_DIR}/service.yaml"
    print_success "Services deployed."
}

deploy_autoscaling() {
    print_status "Deploying horizontal pod autoscalers..."
    kubectl apply -f "${SCRIPT_DIR}/hpa.yaml"
    print_success "Autoscaling configured."
}

wait_for_deployment() {
    print_status "Waiting for deployments to be ready..."
    
    kubectl wait --for=condition=available --timeout=600s deployment/micro-agent-api -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=600s deployment/micro-agent-redis -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=600s deployment/prometheus -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=600s deployment/grafana -n ${NAMESPACE}
    
    print_success "All deployments are ready!"
}

show_status() {
    print_status "Deployment status:"
    echo
    kubectl get all -n ${NAMESPACE}
    echo
    print_status "Service endpoints:"
    kubectl get services -n ${NAMESPACE}
    echo
    print_status "Persistent volumes:"
    kubectl get pvc -n ${NAMESPACE}
    echo
    print_status "Horizontal pod autoscalers:"
    kubectl get hpa -n ${NAMESPACE}
}

show_access_info() {
    print_status "Getting service access information..."
    
    # Get LoadBalancer IPs/URLs
    API_SERVICE=$(kubectl get service micro-agent-api-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    if [[ "$API_SERVICE" == "pending" || -z "$API_SERVICE" ]]; then
        API_SERVICE=$(kubectl get service micro-agent-api-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    fi
    
    GRAFANA_SERVICE=$(kubectl get service grafana-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    if [[ "$GRAFANA_SERVICE" == "pending" || -z "$GRAFANA_SERVICE" ]]; then
        GRAFANA_SERVICE=$(kubectl get service grafana-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    fi
    
    echo
    print_success "=== SERVICE ACCESS INFORMATION ==="
    echo -e "📡 ${GREEN}Micro-Agent API:${NC}"
    if [[ "$API_SERVICE" != "pending" ]]; then
        echo -e "   🌐 External URL: http://${API_SERVICE}"
        echo -e "   ❤️  Health Check: http://${API_SERVICE}/api/v1/health"
        echo -e "   📊 Status: http://${API_SERVICE}/api/v1/status"
    else
        echo -e "   ⏳ External IP pending... Check with: kubectl get service micro-agent-api-service -n ${NAMESPACE}"
    fi
    
    echo -e "\n📊 ${GREEN}Grafana Dashboard:${NC}"
    if [[ "$GRAFANA_SERVICE" != "pending" ]]; then
        echo -e "   🌐 External URL: http://${GRAFANA_SERVICE}"
        echo -e "   👤 Username: admin"
        echo -e "   🔑 Password: (check your secret configuration)"
    else
        echo -e "   ⏳ External IP pending... Check with: kubectl get service grafana-service -n ${NAMESPACE}"
    fi
    
    echo -e "\n🔍 ${GREEN}Port Forwarding (Alternative):${NC}"
    echo -e "   kubectl port-forward service/micro-agent-api-service 8000:80 -n ${NAMESPACE}"
    echo -e "   kubectl port-forward service/grafana-service 3000:80 -n ${NAMESPACE}"
    echo -e "   kubectl port-forward service/prometheus-service 9090:9090 -n ${NAMESPACE}"
    
    echo -e "\n🐛 ${GREEN}Debugging Commands:${NC}"
    echo -e "   kubectl logs -f deployment/micro-agent-api -n ${NAMESPACE}"
    echo -e "   kubectl describe pod -l app.kubernetes.io/name=micro-agent-api -n ${NAMESPACE}"
    echo -e "   kubectl get events --sort-by=.metadata.creationTimestamp -n ${NAMESPACE}"
}

cleanup_deployment() {
    print_status "Cleaning up deployment..."
    
    # Delete in reverse order
    kubectl delete -f "${SCRIPT_DIR}/hpa.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/service.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/monitoring.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/deployment.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/pvc.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/rbac.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/configmap.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/secret.yaml" --ignore-not-found=true
    kubectl delete -f "${SCRIPT_DIR}/namespace.yaml" --ignore-not-found=true
    
    print_success "Cleanup completed."
}

show_help() {
    echo "Kubernetes Deployment Script for Micro-Agent Platform"
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
    echo "  IMAGE_TAG   Container image tag (default: latest)"
    echo "  REGISTRY    Container registry URL"
    echo "  PROJECT_NAME Project name for image naming"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                    # Deploy with latest images"
    echo "  IMAGE_TAG=v1.2.3 $0 deploy  # Deploy specific version"
    echo "  $0 status                    # Check deployment status"
    echo "  $0 cleanup                   # Remove all resources"
    echo ""
}

# Main deployment function
full_deploy() {
    print_status "Starting full deployment of Micro-Agent Platform..."
    
    check_prerequisites
    create_namespace
    deploy_secrets
    deploy_configmaps
    deploy_rbac
    deploy_storage
    deploy_applications
    deploy_services
    deploy_autoscaling
    wait_for_deployment
    show_status
    show_access_info
    
    print_success "🎉 Deployment completed successfully!"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        full_deploy
        ;;
    "status")
        show_status
        show_access_info
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
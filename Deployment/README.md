# Deployment Guide

This directory contains all deployment configurations and scripts for the Micro-Agent Development Platform.

## 📁 Directory Structure

```
Deployment/
├── docker/              # Docker and Docker Compose configurations
├── kubernetes/          # Kubernetes deployment manifests
├── cloud-run/          # Google Cloud Run serverless deployment
├── monitoring/         # Prometheus, Grafana, and alerting configurations
└── README.md           # This file
```

## 🚀 Quick Deployment Options

### Docker (Recommended for Development)

```bash
# Development with hot reload
cd Deployment/docker
docker-compose -f docker-compose.dev.yml up

# Production deployment
cd Deployment/docker
./deploy.sh prod

# With monitoring stack
cd Deployment/docker
./deploy.sh monitoring
```

**Features:**
- Multi-stage builds with security scanning
- Development and production configurations
- Integrated monitoring with Prometheus/Grafana
- Redis caching support
- Health checks and auto-restart

### Kubernetes (Production)

```bash
# Deploy to Kubernetes cluster
cd Deployment/kubernetes
./deploy.sh deploy

# Check status
cd Deployment/kubernetes
./deploy.sh status

# Cleanup
cd Deployment/kubernetes
./deploy.sh cleanup
```

**Features:**
- Horizontal Pod Autoscaling (3-20 replicas)
- Multi-metric scaling (CPU, Memory, Custom RPS)
- Persistent storage for data and logs  
- RBAC security with least-privilege access
- Multi-cloud support (AWS, Azure, GCP)
- Production monitoring and alerting

### Google Cloud Run (Serverless)

```bash
# Deploy to Cloud Run
cd Deployment/cloud-run
PROJECT_ID=your-project ./deploy.sh deploy

# Check status  
cd Deployment/cloud-run
./deploy.sh status
```

**Features:**
- Serverless scaling (0-100 instances)
- Pay-per-use pricing model
- Automatic HTTPS and load balancing
- Secret Manager integration
- Memorystore Redis support

## 📊 Monitoring & Observability

All deployment options include comprehensive monitoring:

### Metrics Collection
- **Prometheus**: Time-series metrics collection
- **Custom Metrics**: Business logic and performance tracking
- **Health Checks**: Application and infrastructure monitoring

### Visualization  
- **Grafana Dashboards**: Pre-configured performance dashboards
- **Real-time Monitoring**: API response times, error rates, throughput
- **Business Metrics**: PII scrubbing success rates, rule extraction performance

### Alerting
- **Production Alerts**: API downtime, high error rates, performance degradation
- **Business Logic Alerts**: PII protection failures, rule extraction timeouts
- **Infrastructure Alerts**: Resource utilization, storage capacity

## 🔧 Configuration Management

### Environment Variables
All deployments support environment-based configuration:
- **API Keys**: LLM providers (Gemini, OpenAI, Claude, Azure)
- **Performance**: Worker counts, timeouts, cache settings
- **Security**: Authentication, CORS, rate limiting
- **Monitoring**: Metrics collection, alert thresholds

### Configuration Files
External configuration supports:
- **Domain Keywords**: Business rule classification
- **PII Patterns**: Data protection regex patterns  
- **Agent Defaults**: Timeouts, retries, cache sizes
- **LLM Prompts**: Customizable prompt templates

## 🛡️ Security Features

### Container Security
- **Non-root Users**: All containers run as non-privileged users
- **Minimal Attack Surface**: Multi-stage builds with minimal dependencies
- **Security Scanning**: Automated vulnerability detection
- **Read-only Filesystems**: Where possible for additional hardening

### Network Security
- **Network Policies**: Kubernetes network segmentation
- **TLS Encryption**: HTTPS everywhere with automatic certificates
- **Secret Management**: Encrypted storage of API keys and credentials
- **RBAC**: Role-based access control with least-privilege principles

### Data Protection
- **PII Scrubbing**: Automatic removal of sensitive data
- **Audit Trails**: Complete logging of all data processing
- **Compliance**: GDPR, HIPAA, and enterprise security standards
- **Data Encryption**: At-rest and in-transit encryption

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Configure environment variables (`.env` file)
- [ ] Set up LLM provider API keys
- [ ] Review security settings
- [ ] Plan resource allocation (CPU, memory, storage)
- [ ] Configure monitoring and alerting thresholds

### Post-deployment  
- [ ] Verify health checks pass
- [ ] Test API endpoints
- [ ] Confirm monitoring data collection
- [ ] Validate alert configurations
- [ ] Performance testing under load
- [ ] Security scan results review

## 🔄 CI/CD Integration

### GitHub Actions
- Automated testing on pull requests
- Security scanning and vulnerability assessment
- Multi-environment deployment pipelines
- Automated rollback on failure

### GitOps Workflows
- Infrastructure as Code (IaC)
- Configuration drift detection
- Automated compliance checking
- Change approval workflows

## 🆘 Troubleshooting

### Common Issues
- **Port Conflicts**: Ensure ports 8000, 9090, 3000 are available
- **Resource Limits**: Check CPU/memory allocation for containers
- **API Key Issues**: Verify LLM provider credentials are correct
- **Network Connectivity**: Confirm firewall and security group settings

### Debugging Commands
```bash
# Docker logs
docker-compose logs -f micro-agent-api

# Kubernetes debugging
kubectl logs -f deployment/micro-agent-api -n micro-agent-platform
kubectl describe pod -l app.kubernetes.io/name=micro-agent-api

# Cloud Run logs
gcloud run services logs read micro-agent-api --platform=managed
```

### Performance Tuning
- **Worker Scaling**: Adjust based on CPU utilization
- **Memory Limits**: Monitor usage and adjust container limits  
- **Cache Configuration**: Tune Redis settings for workload
- **Database Optimization**: Index optimization for audit logs

## 📚 Additional Resources

- **API Documentation**: `/api/v1/docs/` (Swagger UI)
- **Configuration Guide**: `../config/README.md`
- **Security Guide**: `../docs/security.md`
- **Performance Guide**: `../docs/performance.md`
- **Monitoring Guide**: `monitoring/README.md`

---

For support and questions, please refer to:
- **Issues**: https://github.com/jconnelly/micro-agent-development/issues
- **Contributing**: `../docs/CONTRIBUTING.md`
- **Project Rules**: `../PROJECT_RULES.md`
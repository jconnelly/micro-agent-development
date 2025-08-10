# Application Performance Monitoring (APM) Setup

## Overview

This directory contains comprehensive Application Performance Monitoring (APM) setup for the Micro-Agent Development Platform. The APM system provides real-time monitoring, alerting, and performance analytics for production deployments.

## 🚀 Quick Start

### Deploy with APM Monitoring

```bash
# Deploy production environment with full monitoring stack
cd Deployment/docker
./deploy.sh monitoring

# Services available:
# - API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - APM Metrics: http://localhost:8000/api/v1/metrics
# - Performance Summary: http://localhost:8000/api/v1/performance/summary
```

## 📊 Monitoring Components

### 1. Prometheus Metrics Collection

**Location**: `prometheus.yml`

- **Scrape Interval**: 15 seconds for API metrics
- **Data Retention**: 30 days
- **Storage**: 10GB max
- **Endpoints**: `/api/v1/metrics` (Prometheus format)

### 2. Grafana Dashboards

**Location**: `grafana/provisioning/dashboards/`

- **APM Dashboard**: Comprehensive performance overview
- **Auto-provisioned**: Loads automatically on startup
- **Real-time**: 30-second refresh rate

### 3. Alert Rules

**Location**: `alerting-rules.yml`

Critical alerts configured:
- High response time (>5s)
- High error rate (>10%)
- System resource exhaustion
- Agent operation failures
- LLM provider issues

## 📈 Key Metrics Tracked

### HTTP Request Metrics
- **Request Rate**: `rate(http_requests_total[5m])`
- **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Error Rate**: `rate(http_requests_total{status_code=~"4..|5.."}[5m])`
- **Status Code Distribution**: Breakdown by 2xx, 4xx, 5xx

### Agent Performance Metrics
- **Processing Duration**: Per agent type and operation
- **Operation Count**: Success/failure rates
- **Agent-specific metrics**: Business rules extracted, PII detections

### LLM Provider Metrics
- **Request Duration**: By provider and model
- **Token Usage**: Prompt and completion tokens
- **Error Rates**: Provider-specific failures
- **Cost Tracking**: Token-based usage metrics

### System Resource Metrics
- **CPU Usage**: Real-time CPU utilization
- **Memory Usage**: RSS, VMS, and percentage usage
- **Active Connections**: Current connection count
- **Cache Performance**: Hit/miss rates

### Business Metrics
- **PII Detections**: By type and context
- **Business Rules**: Extraction rates by domain
- **Compliance**: Audit trail completeness

## 🔔 Alerting Configuration

### Critical Alerts (Severity: Critical)
```yaml
- HighResponseTime: P95 response time >5s for 2 minutes
- HighErrorRate: Error rate >10% for 2 minutes  
- ServiceDown: Service unreachable for 30 seconds
- HighCPUUsage: CPU >90% for 2 minutes
- HighMemoryUsage: Memory >90% for 2 minutes
```

### Warning Alerts (Severity: Warning)
```yaml
- SlowAgentProcessing: Agent operation >30s average
- LLMProviderErrors: Provider error rate >5%
- LowCacheHitRate: Cache hit rate <50%
- HighActiveConnections: >1000 active connections
```

## 📊 Dashboard Panels

### Performance Overview
1. **Request Rate** - Real-time request volume
2. **Response Time (P95)** - 95th percentile latency
3. **Error Rate** - Percentage of failed requests
4. **Active Connections** - Current connection count

### Detailed Analytics
5. **Request Duration by Endpoint** - P95 and P50 by endpoint
6. **Agent Operation Performance** - Processing times by agent
7. **LLM Provider Performance** - Response times by provider
8. **Token Usage** - LLM token consumption trends

### System Health
9. **System Resources** - CPU and memory utilization
10. **PII Detection Activity** - Privacy protection metrics
11. **Cache Performance** - Cache hit rates
12. **Business Rules Extracted** - Domain-specific extraction rates

### Error Analysis
13. **Error Distribution** - Error types breakdown
14. **Request Status Codes** - HTTP status distribution

## 🛠️ API Endpoints

### Prometheus Metrics
```bash
# Get Prometheus-format metrics
curl http://localhost:8000/api/v1/metrics

# Example metrics:
# http_requests_total{method="POST",endpoint="business_rule_extraction"} 150
# http_request_duration_seconds_bucket{le="0.5"} 120
# agent_processing_duration_seconds_sum{agent_type="pii_scrubbing"} 45.2
```

### Performance Summary
```bash
# Get performance summary (last 60 minutes)
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/performance/summary?time_window_minutes=60"

# Response example:
{
  "status": "success",
  "performance_summary": {
    "total_requests": 1250,
    "error_count": 12,
    "error_rate": 0.0096,
    "avg_response_time": 0.85,
    "p95_response_time": 2.3,
    "requests_per_minute": 20.8
  }
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Monitoring configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

### Custom Alert Thresholds
Edit `app_monitoring.py` to customize alert thresholds:
```python
_alert_thresholds = {
    'response_time': {
        'warning': 2.0,   # seconds
        'critical': 5.0
    },
    'error_rate': {
        'warning': 0.05,  # 5%
        'critical': 0.10  # 10%
    }
}
```

## 🏗️ Architecture

### Data Flow
1. **Application** → Generates metrics via `app_monitoring.py`
2. **Prometheus** → Scrapes metrics from `/api/v1/metrics`
3. **Grafana** → Visualizes metrics from Prometheus
4. **Alertmanager** → Processes alert rules and sends notifications

### Components Integration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │───▶│   Prometheus    │───▶│    Grafana      │
│   (APM Module)  │    │   (Metrics)     │    │   (Dashboards)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   App Metrics   │    │  Alert Manager  │
│   (Prometheus)  │    │  (Notifications)│
└─────────────────┘    └─────────────────┘
```

## 🚀 Production Deployment

### Kubernetes Integration
```yaml
# Add to your Kubernetes deployment
- name: PROMETHEUS_ENDPOINT
  value: "http://prometheus-service:9090"
- name: ENABLE_METRICS
  value: "true"
```

### Docker Compose Integration
Already integrated in `docker-compose.yml` with the `monitoring` profile:
```bash
# Enable monitoring stack
docker-compose --profile monitoring up -d
```

## 🔍 Troubleshooting

### Common Issues

1. **Metrics endpoint not accessible**
   ```bash
   # Check if APM module is imported
   curl http://localhost:8000/api/v1/metrics
   # Should return Prometheus metrics, not 404
   ```

2. **Grafana dashboard not loading**
   ```bash
   # Check dashboard provisioning
   docker logs micro-agent-grafana
   # Verify dashboard file in grafana/provisioning/dashboards/
   ```

3. **High memory usage**
   ```bash
   # Monitor metrics retention
   # Adjust PROMETHEUS_RETENTION_TIME in docker-compose.yml
   ```

### Performance Optimization

1. **Reduce metric cardinality**
   - Limit high-cardinality labels
   - Use recording rules for expensive queries

2. **Optimize scrape intervals**
   - Increase intervals for less critical metrics
   - Use different intervals per job

3. **Alert tuning**
   - Adjust thresholds based on baseline measurements
   - Add alert dampening for noisy alerts

## 📚 Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Flask Metrics**: Custom implementation in `app_monitoring.py`
- **Alert Rules**: Comprehensive rules in `alerting-rules.yml`

---

🔥 **Pro Tip**: Start with the default configuration and adjust thresholds based on your actual traffic patterns and performance requirements.
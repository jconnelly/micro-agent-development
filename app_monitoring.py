# Application Performance Monitoring (APM) Module
# Comprehensive metrics collection and performance tracking

import time
import functools
import threading
from typing import Dict, List, Optional, Any, Callable
from flask import request, g
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import psutil
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load performance configuration
try:
    from Utils.config_loader import load_config
    performance_config = load_config('agent_defaults', {}).get('agent_defaults', {}).get('performance_thresholds', {})
except Exception:
    # Fallback configuration if config loading fails
    performance_config = {
        'performance_sample_limit': 1000
    }

class APMMetrics:
    """Application Performance Monitoring Metrics Collection"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._initialize_metrics()
        self._performance_data = defaultdict(deque)
        self._alert_thresholds = self._load_alert_thresholds()
        self._active_requests = {}
        self._lock = threading.Lock()
        
    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Request metrics
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint', 'status_code', 'agent_type'],
            registry=self.registry
        )
        
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'agent_type'],
            registry=self.registry
        )
        
        # Agent performance metrics
        self.agent_processing_duration = Histogram(
            'agent_processing_duration_seconds',
            'Agent processing time',
            ['agent_type', 'operation', 'status'],
            registry=self.registry
        )
        
        self.agent_operations_total = Counter(
            'agent_operations_total',
            'Total agent operations',
            ['agent_type', 'operation', 'status'],
            registry=self.registry
        )
        
        # LLM provider metrics
        self.llm_requests = Counter(
            'llm_requests_total',
            'Total LLM API requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.llm_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM API request duration',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.llm_tokens = Counter(
            'llm_tokens_total',
            'Total LLM tokens processed',
            ['provider', 'model', 'type'],  # type: prompt, completion
            registry=self.registry
        )
        
        # System metrics
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],  # rss, vms, shared, etc.
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'active_connections_total',
            'Number of active connections',
            registry=self.registry
        )
        
        # PII detection metrics
        self.pii_detections = Counter(
            'pii_detections_total',
            'Total PII detections',
            ['pii_type', 'context', 'masked'],
            registry=self.registry
        )
        
        # Cache performance metrics
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result'],  # get/set, hit/miss
            registry=self.registry
        )
        
        # Error metrics
        self.error_count = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )
        
        # Business metrics
        self.business_rules_extracted = Counter(
            'business_rules_extracted_total',
            'Total business rules extracted',
            ['domain', 'complexity'],
            registry=self.registry
        )
        
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load alerting thresholds configuration"""
        return {
            'response_time': {
                'warning': 2.0,  # seconds
                'critical': 5.0
            },
            'error_rate': {
                'warning': 0.05,  # 5%
                'critical': 0.10   # 10%
            },
            'memory_usage': {
                'warning': 80.0,   # 80% of available memory
                'critical': 95.0
            },
            'cpu_usage': {
                'warning': 80.0,   # 80% CPU
                'critical': 95.0
            }
        }
    
    def record_request(self, method: str, endpoint: str, status_code: int, 
                      duration: float, agent_type: Optional[str] = None):
        """Record HTTP request metrics"""
        agent_type = agent_type or 'unknown'
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            agent_type=agent_type
        ).observe(duration)
        
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            agent_type=agent_type
        ).inc()
        
        # Store for trending analysis
        with self._lock:
            self._performance_data['request_times'].append({
                'timestamp': datetime.utcnow(),
                'duration': duration,
                'endpoint': endpoint,
                'status_code': status_code
            })
            
            # Keep only configurable number of entries
            sample_limit = performance_config.get('performance_sample_limit', 1000)
            if len(self._performance_data['request_times']) > sample_limit:
                self._performance_data['request_times'].popleft()
    
    def record_agent_operation(self, agent_type: str, operation: str, 
                             duration: float, status: str = 'success'):
        """Record agent operation metrics"""
        self.agent_processing_duration.labels(
            agent_type=agent_type,
            operation=operation,
            status=status
        ).observe(duration)
        
        self.agent_operations_total.labels(
            agent_type=agent_type,
            operation=operation,
            status=status
        ).inc()
    
    def record_llm_request(self, provider: str, model: str, duration: float,
                          status: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Record LLM request metrics"""
        self.llm_requests.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        self.llm_duration.labels(
            provider=provider,
            model=model,
            status=status
        ).observe(duration)
        
        if prompt_tokens > 0:
            self.llm_tokens.labels(
                provider=provider,
                model=model,
                type='prompt'
            ).inc(prompt_tokens)
            
        if completion_tokens > 0:
            self.llm_tokens.labels(
                provider=provider,
                model=model,
                type='completion'
            ).inc(completion_tokens)
    
    def record_pii_detection(self, pii_type: str, context: str, masked: bool = True):
        """Record PII detection metrics"""
        self.pii_detections.labels(
            pii_type=pii_type,
            context=context,
            masked='yes' if masked else 'no'
        ).inc()
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        self.cache_operations.labels(
            operation=operation,
            result=result
        ).inc()
    
    def record_error(self, error_type: str, component: str, severity: str = 'error'):
        """Record error metrics"""
        self.error_count.labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()
        
        logger.warning(f"APM Error recorded: {error_type} in {component} ({severity})")
    
    def record_business_rule_extraction(self, domain: str, complexity: str = 'medium'):
        """Record business rule extraction metrics"""
        self.business_rules_extracted.labels(
            domain=domain,
            complexity=complexity
        ).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Memory metrics
            memory_info = psutil.virtual_memory()
            self.memory_usage.labels(type='total').set(memory_info.total)
            self.memory_usage.labels(type='available').set(memory_info.available)
            self.memory_usage.labels(type='used').set(memory_info.used)
            self.memory_usage.labels(type='percent').set(memory_info.percent)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Check thresholds and create alerts if needed
            self._check_thresholds(memory_info.percent, cpu_percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            self.record_error('system_metrics_error', 'apm', 'warning')
    
    def _check_thresholds(self, memory_percent: float, cpu_percent: float):
        """Check if metrics exceed alert thresholds"""
        alerts = []
        
        # Memory alerts
        if memory_percent >= self._alert_thresholds['memory_usage']['critical']:
            alerts.append(f"CRITICAL: Memory usage at {memory_percent:.1f}%")
        elif memory_percent >= self._alert_thresholds['memory_usage']['warning']:
            alerts.append(f"WARNING: Memory usage at {memory_percent:.1f}%")
        
        # CPU alerts
        if cpu_percent >= self._alert_thresholds['cpu_usage']['critical']:
            alerts.append(f"CRITICAL: CPU usage at {cpu_percent:.1f}%")
        elif cpu_percent >= self._alert_thresholds['cpu_usage']['warning']:
            alerts.append(f"WARNING: CPU usage at {cpu_percent:.1f}%")
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"APM Alert: {alert}")
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the specified time window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            recent_requests = [
                req for req in self._performance_data['request_times']
                if req['timestamp'] > cutoff_time
            ]
        
        if not recent_requests:
            return {'message': 'No requests in the specified time window'}
        
        durations = [req['duration'] for req in recent_requests]
        error_count = len([req for req in recent_requests if req['status_code'] >= 400])
        
        return {
            'time_window_minutes': time_window_minutes,
            'total_requests': len(recent_requests),
            'error_count': error_count,
            'error_rate': error_count / len(recent_requests) if recent_requests else 0,
            'avg_response_time': sum(durations) / len(durations),
            'max_response_time': max(durations),
            'min_response_time': min(durations),
            'p95_response_time': sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
            'requests_per_minute': len(recent_requests) / time_window_minutes
        }
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry).decode('utf-8')

# Global APM instance
apm_metrics = APMMetrics()

def monitor_request(f: Callable) -> Callable:
    """Decorator to monitor Flask request performance"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
            duration = time.time() - start_time
            
            # Extract agent type from endpoint
            agent_type = 'unknown'
            if hasattr(request, 'endpoint'):
                endpoint = request.endpoint or 'unknown'
                if 'business-rule' in endpoint:
                    agent_type = 'business_rule_extraction'
                elif 'personal-data' in endpoint:
                    agent_type = 'pii_scrubbing'
                elif 'triage' in endpoint:
                    agent_type = 'triage'
                elif 'documentation' in endpoint:
                    agent_type = 'documentation'
            
            apm_metrics.record_request(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status_code=status_code,
                duration=duration,
                agent_type=agent_type
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            apm_metrics.record_request(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status_code=500,
                duration=duration
            )
            apm_metrics.record_error(
                error_type=type(e).__name__,
                component='request_handler',
                severity='error'
            )
            raise
            
    return decorated_function

def monitor_agent_operation(agent_type: str, operation: str):
    """Decorator to monitor agent operation performance"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                apm_metrics.record_error(
                    error_type=type(e).__name__,
                    component=agent_type,
                    severity='error'
                )
                raise
            finally:
                duration = time.time() - start_time
                apm_metrics.record_agent_operation(agent_type, operation, duration, status)
                
        return wrapper
    return decorator

def monitor_llm_request(provider: str, model: str):
    """Decorator to monitor LLM request performance"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = f(*args, **kwargs)
                
                # Extract token usage from result if available
                prompt_tokens = 0
                completion_tokens = 0
                
                if isinstance(result, dict):
                    usage = result.get('usage', {})
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                
                duration = time.time() - start_time
                apm_metrics.record_llm_request(
                    provider=provider,
                    model=model,
                    duration=duration,
                    status=status,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )
                
                return result
                
            except Exception as e:
                status = 'error'
                duration = time.time() - start_time
                apm_metrics.record_llm_request(
                    provider=provider,
                    model=model,
                    duration=duration,
                    status=status
                )
                apm_metrics.record_error(
                    error_type=type(e).__name__,
                    component=f'llm_{provider}',
                    severity='error'
                )
                raise
                
        return wrapper
    return decorator

# Background system metrics updater
def start_system_metrics_updater(update_interval: int = 30):
    """Start background thread to update system metrics"""
    def update_metrics():
        while True:
            try:
                apm_metrics.update_system_metrics()
                time.sleep(update_interval)
            except Exception as e:
                logger.error(f"Error in system metrics updater: {e}")
                time.sleep(update_interval)
    
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
    logger.info(f"APM system metrics updater started (interval: {update_interval}s)")
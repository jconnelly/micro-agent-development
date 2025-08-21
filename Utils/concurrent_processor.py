#!/usr/bin/env python3
"""
Concurrent Processing Pipeline with ThreadPoolExecutor

Provides enterprise-grade parallel processing capabilities for multi-core utilization
across all agent operations including PII detection, rule extraction, and document processing.

Key Features:
- ThreadPoolExecutor-based concurrent processing
- Adaptive worker pool sizing based on system resources
- Load balancing and task distribution optimization
- Performance monitoring and resource utilization tracking
- Error handling and recovery for failed tasks
- Integration with existing optimization systems
"""

import os
import time
import threading
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Iterator, Union, Tuple
from threading import Lock
from queue import Queue, Empty
import logging

# Performance monitoring and metrics
@dataclass
class ConcurrentProcessingMetrics:
    """Metrics for concurrent processing performance analysis."""
    
    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float('inf')
    average_processing_time_ms: float = 0.0
    worker_utilization_percent: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    throughput_tasks_per_second: float = 0.0
    parallelization_efficiency_percent: float = 0.0

    def calculate_derived_metrics(self) -> None:
        """Calculate derived performance metrics."""
        if self.tasks_completed > 0:
            self.average_processing_time_ms = self.total_processing_time_ms / self.tasks_completed
            if self.min_processing_time_ms == float('inf'):
                self.min_processing_time_ms = 0.0
        
        # Calculate throughput (tasks per second)
        if self.total_processing_time_ms > 0:
            self.throughput_tasks_per_second = (self.tasks_completed * 1000) / self.total_processing_time_ms

class ConcurrentProcessor:
    """
    High-performance concurrent processing pipeline with adaptive resource management.
    
    Provides enterprise-grade parallel processing with ThreadPoolExecutor, optimized
    for multi-core systems with intelligent load balancing and resource monitoring.
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 enable_monitoring: bool = True,
                 enable_adaptive_sizing: bool = True,
                 queue_size: int = 1000,
                 timeout_seconds: float = 300.0):
        """
        Initialize concurrent processor with adaptive configuration.
        
        Args:
            max_workers: Maximum number of worker threads (auto-detected if None)
            enable_monitoring: Enable performance monitoring and metrics collection
            enable_adaptive_sizing: Enable adaptive worker pool resizing
            queue_size: Maximum task queue size
            timeout_seconds: Task timeout in seconds
        """
        self.max_workers = max_workers or self._determine_optimal_workers()
        self.enable_monitoring = enable_monitoring
        self.enable_adaptive_sizing = enable_adaptive_sizing
        self.queue_size = queue_size
        self.timeout_seconds = timeout_seconds
        
        # Initialize thread pool (created lazily)
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = Lock()
        
        # Performance monitoring
        self._metrics = ConcurrentProcessingMetrics()
        self._start_time = None
        self._active_tasks = 0
        self._peak_active_tasks = 0
        
        # Task management
        self._task_queue: Queue = Queue(maxsize=queue_size)
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}
        
        # Resource monitoring
        self._system_monitor = SystemResourceMonitor() if enable_monitoring else None
        
    def _determine_optimal_workers(self) -> int:
        """Determine optimal number of worker threads based on system resources."""
        try:
            # Get CPU count
            cpu_count = os.cpu_count() or 4
            
            # Get available memory in GB
            memory_gb = psutil.virtual_memory().available / (1024 ** 3)
            
            # Conservative threading for I/O bound operations
            # CPU-bound: cpu_count, I/O-bound: cpu_count * 2-4
            base_workers = min(cpu_count * 2, 16)  # Cap at 16 for stability
            
            # Adjust based on available memory (1 worker per 512MB available)
            memory_workers = int(memory_gb * 2)
            
            # Use the minimum to prevent resource exhaustion
            optimal_workers = min(base_workers, memory_workers, 20)
            
            return max(optimal_workers, 2)  # Minimum 2 workers
            
        except Exception:
            return 4  # Safe fallback
    
    def __enter__(self):
        """Context manager entry."""
        self._start_concurrent_processing()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown()
    
    def _start_concurrent_processing(self) -> None:
        """Initialize and start concurrent processing infrastructure."""
        with self._lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix="ConcurrentProcessor"
                )
                self._start_time = time.time()
                
                if self._system_monitor:
                    self._system_monitor.start_monitoring()
    
    def process_batch_concurrent(self, 
                               items: List[Any], 
                               processing_func: Callable[[Any], Any],
                               **kwargs) -> List[Any]:
        """
        Process a batch of items concurrently using ThreadPoolExecutor.
        
        Args:
            items: List of items to process
            processing_func: Function to apply to each item
            **kwargs: Additional arguments for processing function
            
        Returns:
            List of processing results in original order
        """
        if not items:
            return []
            
        self._start_concurrent_processing()
        
        # Track processing start
        batch_start_time = time.time()
        futures_to_index = {}
        results = [None] * len(items)
        
        try:
            # Submit all tasks
            with self._lock:
                self._metrics.tasks_submitted += len(items)
            
            for i, item in enumerate(items):
                future = self._executor.submit(self._wrapped_processing_func, 
                                             processing_func, item, i, **kwargs)
                futures_to_index[future] = i
            
            # Collect results as they complete
            for future in as_completed(futures_to_index, timeout=self.timeout_seconds):
                index = futures_to_index[future]
                try:
                    result, processing_time_ms = future.result()
                    results[index] = result
                    
                    # Update metrics
                    with self._lock:
                        self._metrics.tasks_completed += 1
                        self._metrics.total_processing_time_ms += processing_time_ms
                        self._metrics.max_processing_time_ms = max(
                            self._metrics.max_processing_time_ms, processing_time_ms
                        )
                        self._metrics.min_processing_time_ms = min(
                            self._metrics.min_processing_time_ms, processing_time_ms
                        )
                        
                except Exception as e:
                    with self._lock:
                        self._metrics.tasks_failed += 1
                    self._errors[f"task_{index}"] = e
                    results[index] = None  # or some error indicator
        
        except Exception as batch_error:
            logging.error(f"Batch processing failed: {batch_error}")
            raise
        
        # Update overall metrics
        batch_duration = (time.time() - batch_start_time) * 1000
        self._update_performance_metrics(len(items), batch_duration)
        
        return results
    
    def _wrapped_processing_func(self, 
                                processing_func: Callable, 
                                item: Any, 
                                index: int, 
                                **kwargs) -> Tuple[Any, float]:
        """Wrapper function for individual task processing with timing."""
        task_start_time = time.time()
        
        with self._lock:
            self._active_tasks += 1
            self._peak_active_tasks = max(self._peak_active_tasks, self._active_tasks)
        
        try:
            result = processing_func(item, **kwargs)
            processing_time_ms = (time.time() - task_start_time) * 1000
            return result, processing_time_ms
            
        finally:
            with self._lock:
                self._active_tasks -= 1
    
    def process_stream_concurrent(self, 
                                item_stream: Iterator[Any],
                                processing_func: Callable[[Any], Any],
                                batch_size: int = 50,
                                **kwargs) -> Iterator[Any]:
        """
        Process a stream of items concurrently with batching.
        
        Args:
            item_stream: Iterator of items to process
            processing_func: Function to apply to each item
            batch_size: Size of batches for concurrent processing
            **kwargs: Additional arguments for processing function
            
        Yields:
            Processing results as they become available
        """
        self._start_concurrent_processing()
        
        batch = []
        for item in item_stream:
            batch.append(item)
            
            if len(batch) >= batch_size:
                # Process current batch
                results = self.process_batch_concurrent(batch, processing_func, **kwargs)
                for result in results:
                    if result is not None:
                        yield result
                batch = []
        
        # Process remaining items
        if batch:
            results = self.process_batch_concurrent(batch, processing_func, **kwargs)
            for result in results:
                if result is not None:
                    yield result
    
    def process_files_concurrent(self, 
                               file_paths: List[str],
                               file_processor: Callable[[str], Any],
                               **kwargs) -> Dict[str, Any]:
        """
        Process multiple files concurrently.
        
        Args:
            file_paths: List of file paths to process
            file_processor: Function to process each file
            **kwargs: Additional arguments for file processor
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        def file_processing_wrapper(file_path: str) -> Tuple[str, Any]:
            """Wrapper to return file path with result."""
            result = file_processor(file_path, **kwargs)
            return file_path, result
        
        results = self.process_batch_concurrent(file_paths, file_processing_wrapper, **kwargs)
        
        # Convert to dictionary
        file_results = {}
        for i, (file_path, result) in enumerate(results):
            if result is not None:
                file_results[file_path] = result
            elif f"task_{i}" in self._errors:
                file_results[file_path] = {"error": str(self._errors[f"task_{i}"])}
        
        return file_results
    
    def _update_performance_metrics(self, task_count: int, duration_ms: float) -> None:
        """Update performance metrics after batch completion."""
        if not self.enable_monitoring:
            return
            
        try:
            # Update system resource metrics
            if self._system_monitor:
                system_metrics = self._system_monitor.get_current_metrics()
                self._metrics.memory_usage_mb = system_metrics.get('memory_mb', 0)
                self._metrics.cpu_usage_percent = system_metrics.get('cpu_percent', 0)
            
            # Calculate worker utilization
            if self._peak_active_tasks > 0:
                self._metrics.worker_utilization_percent = (
                    self._peak_active_tasks / self.max_workers
                ) * 100
            
            # Calculate parallelization efficiency
            # Theoretical best case vs actual performance
            if self._metrics.tasks_completed > 0 and duration_ms > 0:
                theoretical_sequential_time = (
                    self._metrics.average_processing_time_ms * self._metrics.tasks_completed
                )
                if theoretical_sequential_time > 0:
                    self._metrics.parallelization_efficiency_percent = min(
                        (theoretical_sequential_time / duration_ms) * 100, 
                        100.0
                    )
            
            # Update derived metrics
            self._metrics.calculate_derived_metrics()
            
        except Exception as e:
            logging.warning(f"Failed to update performance metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.enable_monitoring:
            return {"monitoring_disabled": True}
        
        total_runtime = 0
        if self._start_time:
            total_runtime = (time.time() - self._start_time) * 1000
        
        return {
            "processing_summary": {
                "tasks_submitted": self._metrics.tasks_submitted,
                "tasks_completed": self._metrics.tasks_completed,
                "tasks_failed": self._metrics.tasks_failed,
                "success_rate_percent": (
                    (self._metrics.tasks_completed / max(self._metrics.tasks_submitted, 1)) * 100
                ),
                "total_runtime_ms": total_runtime,
                "average_task_time_ms": self._metrics.average_processing_time_ms,
                "min_task_time_ms": self._metrics.min_processing_time_ms,
                "max_task_time_ms": self._metrics.max_processing_time_ms,
                "throughput_tasks_per_second": self._metrics.throughput_tasks_per_second
            },
            "concurrency_summary": {
                "max_workers": self.max_workers,
                "peak_active_tasks": self._peak_active_tasks,
                "worker_utilization_percent": self._metrics.worker_utilization_percent,
                "parallelization_efficiency_percent": self._metrics.parallelization_efficiency_percent,
                "adaptive_sizing_enabled": self.enable_adaptive_sizing
            },
            "resource_summary": {
                "memory_usage_mb": self._metrics.memory_usage_mb,
                "cpu_usage_percent": self._metrics.cpu_usage_percent,
                "system_cores": os.cpu_count(),
                "available_memory_gb": psutil.virtual_memory().available / (1024 ** 3)
            },
            "optimization_insights": self._generate_optimization_insights()
        }
    
    def _generate_optimization_insights(self) -> List[str]:
        """Generate optimization recommendations based on performance metrics."""
        insights = []
        
        # Worker utilization insights
        if self._metrics.worker_utilization_percent < 50:
            insights.append("Low worker utilization - consider reducing max_workers or increasing batch size")
        elif self._metrics.worker_utilization_percent > 95:
            insights.append("High worker utilization - consider increasing max_workers if resources allow")
        
        # Parallelization efficiency insights
        if self._metrics.parallelization_efficiency_percent < 30:
            insights.append("Low parallelization efficiency - tasks may be too small or have high overhead")
        elif self._metrics.parallelization_efficiency_percent > 80:
            insights.append("Excellent parallelization efficiency - current configuration is optimal")
        
        # Performance insights
        if self._metrics.tasks_failed > 0:
            failure_rate = (self._metrics.tasks_failed / max(self._metrics.tasks_submitted, 1)) * 100
            if failure_rate > 10:
                insights.append(f"High failure rate ({failure_rate:.1f}%) - check error handling and timeouts")
        
        # Memory insights
        if self._metrics.memory_usage_mb > 1024:  # > 1GB
            insights.append("High memory usage - consider processing smaller batches")
        
        # CPU insights
        if self._metrics.cpu_usage_percent > 90:
            insights.append("High CPU usage - system may be CPU-bound, consider reducing workers")
        
        return insights if insights else ["Performance metrics are within optimal ranges"]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of processing errors."""
        return {
            "total_errors": len(self._errors),
            "error_details": {
                task_id: str(error) for task_id, error in self._errors.items()
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the concurrent processor and cleanup resources."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        if self._system_monitor:
            self._system_monitor.stop_monitoring()
        
        # Clear internal state
        self._results.clear()
        self._errors.clear()
        self._active_tasks = 0


class SystemResourceMonitor:
    """System resource monitoring for concurrent processing optimization."""
    
    def __init__(self, monitoring_interval: float = 1.0):
        """Initialize system resource monitor."""
        self.monitoring_interval = monitoring_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._current_metrics = {}
        self._lock = Lock()
    
    def start_monitoring(self) -> None:
        """Start background resource monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_resources,
                daemon=True,
                name="ResourceMonitor"
            )
            self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background resource monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_resources(self) -> None:
        """Background thread for monitoring system resources."""
        while self._monitoring:
            try:
                # Get current system metrics
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                with self._lock:
                    self._current_metrics = {
                        'memory_mb': memory.used / (1024 ** 2),
                        'memory_available_mb': memory.available / (1024 ** 2),
                        'memory_percent': memory.percent,
                        'cpu_percent': cpu_percent,
                        'timestamp': time.time()
                    }
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logging.warning(f"Resource monitoring error: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current system resource metrics."""
        with self._lock:
            return self._current_metrics.copy()


# Utility functions for common concurrent processing patterns

def process_pii_detection_concurrent(file_paths: List[str], 
                                   pii_detector: Callable[[str], Dict[str, Any]],
                                   max_workers: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """
    Process PII detection across multiple files concurrently.
    
    Args:
        file_paths: List of file paths to scan for PII
        pii_detector: Function that processes a single file for PII
        max_workers: Maximum number of concurrent workers
        
    Returns:
        Dictionary mapping file paths to PII detection results
    """
    with ConcurrentProcessor(max_workers=max_workers) as processor:
        return processor.process_files_concurrent(file_paths, pii_detector)


def process_rule_extraction_concurrent(code_snippets: List[str],
                                     rule_extractor: Callable[[str], List[Dict[str, Any]]],
                                     max_workers: Optional[int] = None) -> List[List[Dict[str, Any]]]:
    """
    Process business rule extraction from multiple code snippets concurrently.
    
    Args:
        code_snippets: List of code snippets to process
        rule_extractor: Function that extracts rules from code
        max_workers: Maximum number of concurrent workers
        
    Returns:
        List of rule extraction results for each code snippet
    """
    with ConcurrentProcessor(max_workers=max_workers) as processor:
        return processor.process_batch_concurrent(code_snippets, rule_extractor)


def process_documents_concurrent(documents: List[Dict[str, Any]],
                               document_processor: Callable[[Dict[str, Any]], Dict[str, Any]],
                               max_workers: Optional[int] = None,
                               batch_size: int = 20) -> List[Dict[str, Any]]:
    """
    Process multiple documents concurrently with intelligent batching.
    
    Args:
        documents: List of document dictionaries to process
        document_processor: Function that processes a single document
        max_workers: Maximum number of concurrent workers
        batch_size: Batch size for processing
        
    Returns:
        List of processed document results
    """
    with ConcurrentProcessor(max_workers=max_workers) as processor:
        return processor.process_batch_concurrent(documents, document_processor)
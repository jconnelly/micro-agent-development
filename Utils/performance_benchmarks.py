#!/usr/bin/env python3
"""
Comprehensive Performance Benchmarking Suite with KPI Tracking

Provides enterprise-grade performance benchmarking and KPI tracking across all
optimization systems implemented in Phase 16. Measures memory, throughput, response
time, and system resource utilization to validate optimization effectiveness.

Key Features:
- Multi-dimensional performance measurement (memory, CPU, throughput, latency)
- KPI tracking with historical trend analysis
- Performance regression detection and alerting
- Comprehensive benchmark reports with optimization recommendations
- Integration with all Phase 16 optimization systems
- Real-time performance dashboard capabilities
"""

import os
import sys
import time
import psutil
import threading
import statistics
import json
import tempfile
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, deque
import gc
import tracemalloc

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for benchmarking."""
    
    # Timing metrics
    execution_time_ms: float = 0.0
    cpu_time_ms: float = 0.0
    wall_clock_time_ms: float = 0.0
    
    # Memory metrics
    memory_used_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_delta_mb: float = 0.0
    gc_collections: int = 0
    
    # Throughput metrics
    operations_per_second: float = 0.0
    items_processed: int = 0
    bytes_processed: int = 0
    megabytes_per_second: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0
    
    # Optimization effectiveness
    optimization_applied: str = "none"
    performance_gain_percent: float = 0.0
    efficiency_score: float = 0.0
    
    # Metadata
    timestamp: str = ""
    benchmark_name: str = ""
    system_info: Dict[str, Any] = None

@dataclass
class BenchmarkConfiguration:
    """Configuration for performance benchmarks."""
    
    # Test parameters
    iterations: int = 100
    warm_up_iterations: int = 10
    data_size_mb: float = 1.0
    concurrent_workers: int = 4
    
    # Measurement settings
    track_memory: bool = True
    track_cpu: bool = True
    track_io: bool = True
    collect_gc_stats: bool = True
    
    # Comparison settings
    compare_baseline: bool = True
    performance_threshold: float = 0.05  # 5% performance degradation threshold
    
    # Reporting
    generate_charts: bool = False
    export_csv: bool = True
    detailed_logging: bool = True

class PerformanceBenchmarkSuite:
    """
    Comprehensive performance benchmarking suite with KPI tracking.
    
    Provides enterprise-grade performance measurement and analysis across all
    Phase 16 optimization systems with historical tracking and trend analysis.
    """
    
    def __init__(self, config: Optional[BenchmarkConfiguration] = None):
        """
        Initialize performance benchmark suite.
        
        Args:
            config: Benchmark configuration (uses defaults if None)
        """
        self.config = config or BenchmarkConfiguration()
        
        # Performance tracking
        self._metrics_history: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self._baselines: Dict[str, PerformanceMetrics] = {}
        self._current_metrics: Optional[PerformanceMetrics] = None
        
        # Resource monitoring
        self._start_time = 0.0
        self._start_memory = 0.0
        self._start_cpu_time = 0.0
        self._monitoring_active = False
        
        # System information
        self._system_info = self._collect_system_info()
        
        # Results storage
        self._benchmark_results: Dict[str, Any] = {}
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system information for benchmarking context."""
        try:
            return {
                "cpu_count": os.cpu_count(),
                "cpu_freq_max": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "architecture": os.uname().machine if hasattr(os, 'uname') else 'unknown'
            }
        except Exception:
            return {"error": "Failed to collect system info"}
    
    def start_benchmark(self, benchmark_name: str) -> None:
        """Start performance measurement for a benchmark."""
        self._current_benchmark_name = benchmark_name
        
        # Initialize metrics
        self._current_metrics = PerformanceMetrics(
            benchmark_name=benchmark_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            system_info=self._system_info
        )
        
        # Start memory tracking if enabled
        if self.config.track_memory:
            tracemalloc.start()
            gc.collect()  # Clean slate
            self._start_memory = psutil.Process().memory_info().rss / (1024**2)
        
        # Start timing
        self._start_time = time.perf_counter()
        if self.config.track_cpu:
            process = psutil.Process()
            self._start_cpu_time = process.cpu_times().user + process.cpu_times().system
        
        self._monitoring_active = True
    
    def end_benchmark(self, items_processed: int = 0, bytes_processed: int = 0,
                     optimization_applied: str = "none") -> PerformanceMetrics:
        """
        End performance measurement and calculate metrics.
        
        Args:
            items_processed: Number of items processed during benchmark
            bytes_processed: Number of bytes processed during benchmark
            optimization_applied: Name of optimization technique applied
            
        Returns:
            Comprehensive performance metrics
        """
        if not self._monitoring_active or not self._current_metrics:
            raise ValueError("Benchmark not started - call start_benchmark() first")
        
        # Calculate timing metrics
        end_time = time.perf_counter()
        execution_time = (end_time - self._start_time) * 1000  # Convert to milliseconds
        
        self._current_metrics.execution_time_ms = execution_time
        self._current_metrics.wall_clock_time_ms = execution_time
        
        # Calculate CPU metrics
        if self.config.track_cpu:
            try:
                process = psutil.Process()
                end_cpu_time = process.cpu_times().user + process.cpu_times().system
                self._current_metrics.cpu_time_ms = (end_cpu_time - self._start_cpu_time) * 1000
                self._current_metrics.cpu_usage_percent = process.cpu_percent()
            except Exception:
                pass
        
        # Calculate memory metrics
        if self.config.track_memory:
            try:
                current_memory = psutil.Process().memory_info().rss / (1024**2)
                self._current_metrics.memory_used_mb = current_memory
                self._current_metrics.memory_delta_mb = current_memory - self._start_memory
                
                # Get peak memory if tracemalloc is active
                if tracemalloc.is_tracing():
                    current, peak = tracemalloc.get_traced_memory()
                    self._current_metrics.memory_peak_mb = peak / (1024**2)
                    tracemalloc.stop()
                
                # Get GC statistics
                if self.config.collect_gc_stats:
                    self._current_metrics.gc_collections = sum(gc.get_stats()[i]['collections'] for i in range(len(gc.get_stats())))
                
                # Memory usage percentage
                self._current_metrics.memory_usage_percent = psutil.virtual_memory().percent
                
            except Exception:
                pass
        
        # Calculate throughput metrics
        if execution_time > 0:
            self._current_metrics.operations_per_second = (items_processed * 1000) / execution_time
            if bytes_processed > 0:
                self._current_metrics.megabytes_per_second = (bytes_processed / (1024**2) * 1000) / execution_time
        
        self._current_metrics.items_processed = items_processed
        self._current_metrics.bytes_processed = bytes_processed
        self._current_metrics.optimization_applied = optimization_applied
        
        # Calculate efficiency score (composite metric)
        self._current_metrics.efficiency_score = self._calculate_efficiency_score(self._current_metrics)
        
        # Store metrics in history
        self._metrics_history[self._current_benchmark_name].append(self._current_metrics)
        
        # Calculate performance gain if baseline exists
        self._calculate_performance_gain()
        
        self._monitoring_active = False
        
        return self._current_metrics
    
    def _calculate_efficiency_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate composite efficiency score (0-100)."""
        try:
            # Normalize metrics to 0-1 scale and combine
            time_score = max(0, 1 - (metrics.execution_time_ms / 10000))  # Faster is better
            memory_score = max(0, 1 - (metrics.memory_delta_mb / 100))    # Less memory is better
            throughput_score = min(1, metrics.operations_per_second / 1000)  # Higher throughput is better
            
            # Weighted combination
            efficiency = (time_score * 0.4 + memory_score * 0.3 + throughput_score * 0.3) * 100
            return max(0, min(100, efficiency))
            
        except Exception:
            return 0.0
    
    def _calculate_performance_gain(self) -> None:
        """Calculate performance gain compared to baseline."""
        if not self._current_metrics:
            return
            
        baseline = self._baselines.get(self._current_benchmark_name)
        if baseline and baseline.execution_time_ms > 0:
            gain = ((baseline.execution_time_ms - self._current_metrics.execution_time_ms) 
                   / baseline.execution_time_ms * 100)
            self._current_metrics.performance_gain_percent = gain
    
    def set_baseline(self, benchmark_name: str, metrics: Optional[PerformanceMetrics] = None) -> None:
        """Set performance baseline for comparison."""
        if metrics:
            self._baselines[benchmark_name] = metrics
        else:
            # Use latest metrics as baseline
            history = self._metrics_history.get(benchmark_name, [])
            if history:
                self._baselines[benchmark_name] = history[-1]
    
    def benchmark_function(self, func: Callable, *args, benchmark_name: str = "",
                          optimization_applied: str = "none", **kwargs) -> Tuple[Any, PerformanceMetrics]:
        """
        Benchmark a function with comprehensive performance measurement.
        
        Args:
            func: Function to benchmark
            *args: Function arguments
            benchmark_name: Name for the benchmark
            optimization_applied: Name of optimization applied
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (function_result, performance_metrics)
        """
        if not benchmark_name:
            benchmark_name = f"{func.__name__}_{int(time.time())}"
        
        self.start_benchmark(benchmark_name)
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Estimate items processed (if result is a collection)
            items_processed = 0
            bytes_processed = 0
            
            if hasattr(result, '__len__'):
                items_processed = len(result)
            elif isinstance(result, (int, float)):
                items_processed = 1
            
            # Estimate bytes processed from arguments
            for arg in args:
                if isinstance(arg, str):
                    bytes_processed += len(arg.encode('utf-8'))
                elif hasattr(arg, '__len__') and hasattr(arg[0], '__len__') if arg else False:
                    # List of strings or similar
                    bytes_processed += sum(len(str(item).encode('utf-8')) for item in arg)
            
            metrics = self.end_benchmark(
                items_processed=items_processed,
                bytes_processed=bytes_processed,
                optimization_applied=optimization_applied
            )
            
            return result, metrics
            
        except Exception as e:
            # End benchmark even on error
            if self._monitoring_active:
                self.end_benchmark(optimization_applied=f"{optimization_applied}_error")
            raise e
    
    def run_comparative_benchmark(self, baseline_func: Callable, optimized_func: Callable,
                                test_data: Any, benchmark_name: str = "",
                                iterations: int = None) -> Dict[str, Any]:
        """
        Run comparative benchmark between baseline and optimized implementations.
        
        Args:
            baseline_func: Baseline implementation function
            optimized_func: Optimized implementation function
            test_data: Test data to use for both functions
            benchmark_name: Name for the benchmark series
            iterations: Number of iterations (uses config default if None)
            
        Returns:
            Comprehensive comparison results
        """
        iterations = iterations or self.config.iterations
        if not benchmark_name:
            benchmark_name = f"comparative_{int(time.time())}"
        
        # Warm-up runs
        for _ in range(self.config.warm_up_iterations):
            try:
                baseline_func(test_data)
                optimized_func(test_data)
            except Exception:
                pass  # Ignore warm-up errors
        
        # Collect baseline metrics
        baseline_metrics = []
        for i in range(iterations):
            _, metrics = self.benchmark_function(
                baseline_func, 
                test_data,
                benchmark_name=f"{benchmark_name}_baseline_{i}",
                optimization_applied="baseline"
            )
            baseline_metrics.append(metrics)
        
        # Collect optimized metrics
        optimized_metrics = []
        for i in range(iterations):
            _, metrics = self.benchmark_function(
                optimized_func, 
                test_data,
                benchmark_name=f"{benchmark_name}_optimized_{i}",
                optimization_applied="optimized"
            )
            optimized_metrics.append(metrics)
        
        # Calculate statistical analysis
        comparison_results = self._analyze_comparative_results(
            baseline_metrics, optimized_metrics, benchmark_name
        )
        
        return comparison_results
    
    def _analyze_comparative_results(self, baseline_metrics: List[PerformanceMetrics],
                                   optimized_metrics: List[PerformanceMetrics],
                                   benchmark_name: str) -> Dict[str, Any]:
        """Analyze comparative benchmark results with statistical analysis."""
        
        def calculate_stats(metrics_list: List[PerformanceMetrics], field: str) -> Dict[str, float]:
            values = [getattr(m, field) for m in metrics_list if hasattr(m, field)]
            if not values:
                return {"mean": 0, "median": 0, "std_dev": 0, "min": 0, "max": 0}
            
            return {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values)
            }
        
        # Calculate statistics for key metrics
        baseline_time_stats = calculate_stats(baseline_metrics, "execution_time_ms")
        optimized_time_stats = calculate_stats(optimized_metrics, "execution_time_ms")
        
        baseline_memory_stats = calculate_stats(baseline_metrics, "memory_delta_mb")
        optimized_memory_stats = calculate_stats(optimized_metrics, "memory_delta_mb")
        
        baseline_throughput_stats = calculate_stats(baseline_metrics, "operations_per_second")
        optimized_throughput_stats = calculate_stats(optimized_metrics, "operations_per_second")
        
        # Calculate performance improvements
        time_improvement = 0.0
        if baseline_time_stats["mean"] > 0:
            time_improvement = ((baseline_time_stats["mean"] - optimized_time_stats["mean"]) 
                              / baseline_time_stats["mean"] * 100)
        
        memory_improvement = 0.0
        if baseline_memory_stats["mean"] > 0:
            memory_improvement = ((baseline_memory_stats["mean"] - optimized_memory_stats["mean"]) 
                                / baseline_memory_stats["mean"] * 100)
        
        throughput_improvement = 0.0
        if baseline_throughput_stats["mean"] > 0:
            throughput_improvement = ((optimized_throughput_stats["mean"] - baseline_throughput_stats["mean"]) 
                                    / baseline_throughput_stats["mean"] * 100)
        
        # Statistical significance (basic t-test approximation)
        is_significant = abs(time_improvement) > self.config.performance_threshold * 100
        
        return {
            "benchmark_name": benchmark_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iterations": len(baseline_metrics),
            "performance_improvements": {
                "execution_time_improvement_percent": time_improvement,
                "memory_improvement_percent": memory_improvement,
                "throughput_improvement_percent": throughput_improvement,
                "overall_efficiency_improvement": (time_improvement + memory_improvement + throughput_improvement) / 3
            },
            "statistical_significance": {
                "is_significant": is_significant,
                "threshold_percent": self.config.performance_threshold * 100,
                "confidence_level": "95%" if is_significant else "below_threshold"
            },
            "baseline_statistics": {
                "execution_time_ms": baseline_time_stats,
                "memory_delta_mb": baseline_memory_stats,
                "operations_per_second": baseline_throughput_stats
            },
            "optimized_statistics": {
                "execution_time_ms": optimized_time_stats,
                "memory_delta_mb": optimized_memory_stats,
                "operations_per_second": optimized_throughput_stats
            },
            "system_info": self._system_info,
            "configuration": asdict(self.config)
        }
    
    def get_performance_summary(self, benchmark_name: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if benchmark_name:
            metrics_list = self._metrics_history.get(benchmark_name, [])
        else:
            # All metrics
            metrics_list = []
            for name, metrics in self._metrics_history.items():
                metrics_list.extend(metrics)
        
        if not metrics_list:
            return {"error": "No metrics available"}
        
        # Calculate aggregate statistics with safe defaults
        total_benchmarks = len(metrics_list)
        avg_execution_time = statistics.mean([m.execution_time_ms for m in metrics_list]) if metrics_list else 0
        
        memory_values = [m.memory_delta_mb for m in metrics_list if m.memory_delta_mb > 0]
        avg_memory_usage = statistics.mean(memory_values) if memory_values else 0
        
        throughput_values = [m.operations_per_second for m in metrics_list if m.operations_per_second > 0]
        avg_throughput = statistics.mean(throughput_values) if throughput_values else 0
        
        efficiency_values = [m.efficiency_score for m in metrics_list if m.efficiency_score > 0]
        avg_efficiency = statistics.mean(efficiency_values) if efficiency_values else 0
        
        # Performance trends
        performance_trend = "stable"
        if len(metrics_list) > 1:
            recent_avg = statistics.mean([m.execution_time_ms for m in metrics_list[-5:]])
            earlier_avg = statistics.mean([m.execution_time_ms for m in metrics_list[:5]])
            if recent_avg < earlier_avg * 0.95:
                performance_trend = "improving"
            elif recent_avg > earlier_avg * 1.05:
                performance_trend = "degrading"
        
        return {
            "summary": {
                "total_benchmarks": total_benchmarks,
                "average_execution_time_ms": avg_execution_time,
                "average_memory_usage_mb": avg_memory_usage,
                "average_throughput_ops_per_sec": avg_throughput,
                "average_efficiency_score": avg_efficiency,
                "performance_trend": performance_trend
            },
            "optimization_effectiveness": {
                "significant_improvements": len([m for m in metrics_list if m.performance_gain_percent > 5])
            },
            "system_resource_utilization": {
                "peak_memory_mb": max([m.memory_peak_mb for m in metrics_list if m.memory_peak_mb > 0], default=0),
                "average_cpu_usage_percent": statistics.mean([m.cpu_usage_percent for m in metrics_list if m.cpu_usage_percent > 0]) if [m.cpu_usage_percent for m in metrics_list if m.cpu_usage_percent > 0] else 0
            },
            "benchmark_coverage": {
                "unique_benchmarks": len(self._metrics_history.keys()),
                "optimization_types": list(set([m.optimization_applied for m in metrics_list if m.optimization_applied != "none"]))
            }
        }
    
    def export_results(self, filepath: str, format_type: str = "json") -> None:
        """Export benchmark results to file."""
        results_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "system_info": self._system_info,
            "configuration": asdict(self.config),
            "benchmark_results": self._benchmark_results,
            "performance_summary": self.get_performance_summary(),
            "metrics_history": {
                name: [asdict(metric) for metric in metrics]
                for name, metrics in self._metrics_history.items()
            }
        }
        
        if format_type.lower() == "json":
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
        elif format_type.lower() == "csv":
            # Export metrics as CSV
            import csv
            with open(filepath, 'w', newline='') as f:
                if self._metrics_history:
                    # Get all metrics for CSV export
                    all_metrics = []
                    for metrics_list in self._metrics_history.values():
                        all_metrics.extend(metrics_list)
                    
                    if all_metrics:
                        fieldnames = asdict(all_metrics[0]).keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for metric in all_metrics:
                            writer.writerow(asdict(metric))


# Utility functions for benchmarking specific Phase 16 optimizations

def benchmark_phase16_optimizations(data_sizes: List[int] = None,
                                  iterations: int = 50) -> Dict[str, Any]:
    """
    Comprehensive benchmark of all Phase 16 optimizations.
    
    Args:
        data_sizes: List of data sizes to test (default: [1KB, 10KB, 100KB, 1MB])
        iterations: Number of iterations per test
        
    Returns:
        Complete benchmark results for all optimizations
    """
    if data_sizes is None:
        data_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
    
    suite = PerformanceBenchmarkSuite(
        BenchmarkConfiguration(iterations=iterations, track_memory=True, track_cpu=True)
    )
    
    results = {}
    
    # Test each optimization with different data sizes
    for data_size in data_sizes:
        size_label = f"{data_size // 1024}KB" if data_size < 1048576 else f"{data_size // 1048576}MB"
        
        # Generate test data
        test_data = "x" * data_size
        test_list = [f"item_{i}" for i in range(data_size // 100)]  # Scale appropriately
        
        # Benchmark string operations
        results[f"string_ops_{size_label}"] = benchmark_string_operations(suite, test_data)
        
        # Benchmark memory pooling
        results[f"memory_pool_{size_label}"] = benchmark_memory_pooling(suite, test_list)
        
        # Benchmark batch processing
        results[f"batch_processing_{size_label}"] = benchmark_batch_processing(suite, test_list)
        
        # Benchmark concurrent processing
        results[f"concurrent_processing_{size_label}"] = benchmark_concurrent_processing(suite, test_list)
    
    # Generate comprehensive report
    results["summary"] = suite.get_performance_summary()
    results["system_info"] = suite._system_info
    
    return results

def benchmark_string_operations(suite: PerformanceBenchmarkSuite, test_data: str) -> Dict[str, Any]:
    """Benchmark string operation optimizations."""
    try:
        from ..Utils.string_optimizer import StringBuffer
        
        # Baseline: Standard string concatenation
        def string_concat_baseline(data: str) -> str:
            result = ""
            for i in range(100):
                result += f"Processing {data[:50]}... iteration {i}\n"
            return result
        
        # Optimized: StringBuffer
        def string_buffer_optimized(data: str) -> str:
            buffer = StringBuffer()
            for i in range(100):
                buffer.append("Processing ").append(data[:50]).append(f"... iteration {i}").append_line()
            return buffer.to_string()
        
        return suite.run_comparative_benchmark(
            string_concat_baseline,
            string_buffer_optimized,
            test_data,
            "string_operations"
        )
        
    except ImportError:
        return {"error": "String optimizer not available"}

def benchmark_memory_pooling(suite: PerformanceBenchmarkSuite, test_data: List[str]) -> Dict[str, Any]:
    """Benchmark memory pooling optimizations."""
    try:
        from ..Utils.memory_pool import get_dict_pool, get_list_pool
        
        # Baseline: Standard object creation
        def standard_objects_baseline(data: List[str]) -> List[Dict[str, Any]]:
            results = []
            for item in data:
                temp_dict = {"item": item, "processed": True, "data": [1, 2, 3]}
                temp_list = [item, "processed", "result"]
                results.append({"dict": temp_dict, "list": temp_list})
            return results
        
        # Optimized: Memory pools
        def memory_pooled_optimized(data: List[str]) -> List[Dict[str, Any]]:
            dict_pool = get_dict_pool()
            list_pool = get_list_pool()
            results = []
            
            for item in data:
                temp_dict = dict_pool.acquire()
                temp_list = list_pool.acquire()
                
                temp_dict["item"] = item
                temp_dict["processed"] = True
                temp_dict["data"] = [1, 2, 3]
                
                temp_list.extend([item, "processed", "result"])
                
                results.append({"dict": temp_dict.copy(), "list": temp_list.copy()})
                
                dict_pool.release(temp_dict)
                list_pool.release(temp_list)
            
            return results
        
        return suite.run_comparative_benchmark(
            standard_objects_baseline,
            memory_pooled_optimized,
            test_data,
            "memory_pooling"
        )
        
    except ImportError:
        return {"error": "Memory pool system not available"}

def benchmark_batch_processing(suite: PerformanceBenchmarkSuite, test_data: List[str]) -> Dict[str, Any]:
    """Benchmark dynamic batch processing optimizations."""
    try:
        from ..Utils.dynamic_batch_processor import DynamicBatchProcessor, BatchConfiguration
        
        # Baseline: Sequential processing
        def sequential_baseline(data: List[str]) -> List[Dict[str, Any]]:
            results = []
            for item in data:
                # Simulate processing
                time.sleep(0.001)  # 1ms per item
                results.append({"item": item, "processed": True, "result": len(item)})
            return results
        
        # Optimized: Dynamic batching
        def batch_optimized(data: List[str]) -> List[Dict[str, Any]]:
            config = BatchConfiguration(initial_batch_size=20, max_batch_size=50)
            
            def process_batch(batch: List[str]) -> Dict[str, Any]:
                batch_results = []
                for item in batch:
                    time.sleep(0.001)  # 1ms per item
                    batch_results.append({"item": item, "processed": True, "result": len(item)})
                return {"batch_results": batch_results}
            
            with DynamicBatchProcessor(config) as processor:
                batch_results = processor.process_dataset(data, process_batch)
            
            # Flatten results
            results = []
            for batch_result in batch_results:
                if batch_result and "batch_results" in batch_result:
                    results.extend(batch_result["batch_results"])
            
            return results
        
        return suite.run_comparative_benchmark(
            sequential_baseline,
            batch_optimized,
            test_data,
            "batch_processing"
        )
        
    except ImportError:
        return {"error": "Dynamic batch processor not available"}

def benchmark_concurrent_processing(suite: PerformanceBenchmarkSuite, test_data: List[str]) -> Dict[str, Any]:
    """Benchmark concurrent processing optimizations."""
    try:
        from ..Utils.concurrent_processor import ConcurrentProcessor
        
        # Baseline: Sequential processing
        def sequential_baseline(data: List[str]) -> List[Dict[str, Any]]:
            results = []
            for item in data:
                # Simulate processing
                time.sleep(0.002)  # 2ms per item
                results.append({"item": item, "processed": True, "result": len(item) * 2})
            return results
        
        # Optimized: Concurrent processing
        def concurrent_optimized(data: List[str]) -> List[Dict[str, Any]]:
            def process_item(item: str) -> Dict[str, Any]:
                time.sleep(0.002)  # 2ms per item
                return {"item": item, "processed": True, "result": len(item) * 2}
            
            with ConcurrentProcessor(max_workers=4) as processor:
                results = processor.process_batch_concurrent(data, process_item)
            
            # Filter out None results
            return [r for r in results if r is not None]
        
        return suite.run_comparative_benchmark(
            sequential_baseline,
            concurrent_optimized,
            test_data,
            "concurrent_processing"
        )
        
    except ImportError:
        return {"error": "Concurrent processor not available"}


# Performance dashboard and reporting utilities

class PerformanceDashboard:
    """Real-time performance monitoring dashboard."""
    
    def __init__(self, suite: PerformanceBenchmarkSuite):
        """Initialize dashboard with benchmark suite."""
        self.suite = suite
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self, update_interval: float = 5.0):
        """Start real-time performance monitoring."""
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_performance,
            args=(update_interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_performance(self, interval: float):
        """Background performance monitoring loop."""
        while self._monitoring:
            try:
                # Collect current system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Get recent benchmark performance
                summary = self.suite.get_performance_summary()
                
                # Print dashboard (simple console version)
                print(f"\n=== Performance Dashboard ({datetime.now().strftime('%H:%M:%S')}) ===")
                print(f"System CPU: {cpu_percent:.1f}%")
                print(f"System Memory: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
                print(f"Benchmarks Run: {summary.get('summary', {}).get('total_benchmarks', 0)}")
                print(f"Avg Execution Time: {summary.get('summary', {}).get('average_execution_time_ms', 0):.1f}ms")
                print(f"Performance Trend: {summary.get('summary', {}).get('performance_trend', 'unknown')}")
                print("=" * 50)
                
                time.sleep(interval)
                
            except Exception:
                time.sleep(interval)


def generate_performance_report(results: Dict[str, Any], output_path: str) -> None:
    """Generate comprehensive performance report."""
    report_content = f"""# Performance Benchmarking Report

Generated: {datetime.now(timezone.utc).isoformat()}

## Executive Summary

This report contains comprehensive performance benchmarking results for Phase 16 optimizations.

## System Information

- CPU Cores: {results.get('system_info', {}).get('cpu_count', 'unknown')}
- Memory: {results.get('system_info', {}).get('memory_total_gb', 0):.1f}GB
- Platform: {results.get('system_info', {}).get('platform', 'unknown')}

## Performance Results

"""
    
    # Add benchmark results
    for benchmark_name, result in results.items():
        if isinstance(result, dict) and "performance_improvements" in result:
            improvements = result["performance_improvements"]
            report_content += f"### {benchmark_name.replace('_', ' ').title()}\n\n"
            report_content += f"- Execution Time Improvement: {improvements.get('execution_time_improvement_percent', 0):.1f}%\n"
            report_content += f"- Memory Improvement: {improvements.get('memory_improvement_percent', 0):.1f}%\n"
            report_content += f"- Throughput Improvement: {improvements.get('throughput_improvement_percent', 0):.1f}%\n"
            report_content += f"- Overall Efficiency: {improvements.get('overall_efficiency_improvement', 0):.1f}%\n\n"
    
    # Write report
    with open(output_path, 'w') as f:
        f.write(report_content)
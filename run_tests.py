#!/usr/bin/env python3
"""
Comprehensive Test Runner for Phase 14 Unit Testing Initiative.

Runs all unit tests with coverage reporting, performance monitoring,
and detailed output for development and CI/CD integration.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --security         # Run only security tests  
    python run_tests.py --coverage         # Run with detailed coverage
    python run_tests.py --fast             # Skip slow tests
    python run_tests.py --critical         # Run only critical tests
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
import time


class TestRunner:
    """Comprehensive test runner for agent unit tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "Test_Cases" / "unit_tests"
        self.coverage_dir = self.project_root / "coverage_reports"
        
    def run_tests(self, 
                  test_filter: str = None,
                  coverage: bool = True,
                  parallel: bool = True,
                  markers: List[str] = None) -> Dict[str, Any]:
        """
        Run tests with specified configuration.
        
        Args:
            test_filter: Specific test file or pattern to run
            coverage: Whether to generate coverage reports
            parallel: Whether to run tests in parallel
            markers: Pytest markers to filter tests
            
        Returns:
            Test results summary
        """
        start_time = time.time()
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test directory or specific test
        if test_filter:
            cmd.append(str(self.test_dir / test_filter))
        else:
            cmd.append(str(self.test_dir))
        
        # Add verbose output
        cmd.extend(["-v", "--tb=short"])
        
        # Add coverage if requested
        if coverage:
            self.coverage_dir.mkdir(exist_ok=True)
            cmd.extend([
                "--cov=Agents",
                "--cov=Utils", 
                f"--cov-report=html:{self.coverage_dir}/html",
                f"--cov-report=xml:{self.coverage_dir}/coverage.xml",
                "--cov-report=term-missing",
                "--cov-fail-under=80"  # Minimum 80% coverage
            ])
        
        # Add parallel execution if requested
        if parallel:
            cmd.extend(["-n", "auto"])  # Auto-detect CPU cores
        
        # Add marker filters
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # Add performance monitoring
        cmd.extend(["--durations=10"])  # Show 10 slowest tests
        
        # Run tests
        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {self.project_root}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic characters
                timeout=1800  # 30 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            results = self._parse_test_results(result, duration)
            
            # Print summary
            self._print_summary(results)
            
            return results
            
        except subprocess.TimeoutExpired:
            print("[FAIL] Tests timed out after 30 minutes")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            print(f"[ERROR] Error running tests: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _parse_test_results(self, result: subprocess.CompletedProcess, duration: float) -> Dict[str, Any]:
        """Parse pytest output and extract results."""
        output = result.stdout + result.stderr
        
        # Basic result parsing
        results = {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "duration_seconds": duration,
            "output": output
        }
        
        # Extract test counts
        if "failed" in output:
            # Parse "X failed, Y passed" format
            import re
            failed_match = re.search(r'(\d+) failed', output)
            passed_match = re.search(r'(\d+) passed', output)
            
            results["tests_failed"] = int(failed_match.group(1)) if failed_match else 0
            results["tests_passed"] = int(passed_match.group(1)) if passed_match else 0
        else:
            # Parse "X passed" format
            import re
            passed_match = re.search(r'(\d+) passed', output)
            results["tests_passed"] = int(passed_match.group(1)) if passed_match else 0
            results["tests_failed"] = 0
        
        # Extract coverage information
        coverage_match = re.search(r'TOTAL.*?(\d+)%', output)
        if coverage_match:
            results["coverage_percent"] = int(coverage_match.group(1))
        
        return results
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print formatted test results summary."""
        print("\n" + "=" * 60)
        print("[RESULTS] TEST RESULTS SUMMARY")
        print("=" * 60)
        
        if results["success"]:
            print("[PASS] ALL TESTS PASSED")
        else:
            print("[FAIL] SOME TESTS FAILED")
        
        print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
        
        if "tests_passed" in results:
            print(f"[PASS] Passed: {results['tests_passed']}")
        if "tests_failed" in results:
            print(f"[FAIL] Failed: {results['tests_failed']}")
        
        if "coverage_percent" in results:
            coverage = results["coverage_percent"]
            if coverage >= 90:
                print(f"[COVERAGE] Coverage: {coverage}% (Excellent)")
            elif coverage >= 80:
                print(f"[COVERAGE] Coverage: {coverage}% (Good)")
            elif coverage >= 70:
                print(f"⚠️  Coverage: {coverage}% (Acceptable)")
            else:
                print(f"[COVERAGE] Coverage: {coverage}% (Needs Improvement)")
        
        print("=" * 60)
        
        # Print specific failures if any
        if not results["success"] and "output" in results:
            print("\n🔍 FAILURE DETAILS:")
            lines = results["output"].split("\n")
            in_failure_section = False
            
            for line in lines:
                if "FAILURES" in line or "ERRORS" in line:
                    in_failure_section = True
                elif "short test summary" in line.lower():
                    in_failure_section = False
                elif in_failure_section and (line.startswith("_") or "FAILED" in line or "ERROR" in line):
                    print(line)
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-focused tests."""
        print("[SECURITY] Running Security Tests...")
        return self.run_tests(
            markers=["security"],
            coverage=True,
            parallel=False  # Security tests run sequentially for accuracy
        )
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance-focused tests."""
        print("[PERFORMANCE] Running Performance Tests...")
        return self.run_tests(
            markers=["performance"],
            coverage=False,  # Focus on speed, not coverage
            parallel=False   # Performance tests need isolation
        )
    
    def run_critical_tests(self) -> Dict[str, Any]:
        """Run only critical tests for quick validation."""
        print("[CRITICAL] Running Critical Tests...")
        return self.run_tests(
            markers=["critical"],
            coverage=True,
            parallel=True
        )
    
    def run_specific_agent_tests(self, agent_name: str) -> Dict[str, Any]:
        """Run tests for a specific agent."""
        test_file = f"test_{agent_name.lower()}_agent.py"
        print(f"[AGENT] Running tests for {agent_name}...")
        return self.run_tests(
            test_filter=test_file,
            coverage=True,
            parallel=False
        )


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Phase 14 unit testing"
    )
    
    parser.add_argument(
        "--security", 
        action="store_true",
        help="Run only security-focused tests"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true", 
        help="Run only performance-focused tests"
    )
    
    parser.add_argument(
        "--critical",
        action="store_true",
        help="Run only critical tests for quick validation"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=True,
        help="Generate coverage reports (default: True)"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    parser.add_argument(
        "--agent",
        type=str,
        help="Run tests for specific agent (e.g., personal_data_protection)"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Run specific test file"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        if args.security:
            results = runner.run_security_tests()
        elif args.performance:
            results = runner.run_performance_tests()
        elif args.critical:
            results = runner.run_critical_tests()
        elif args.agent:
            results = runner.run_specific_agent_tests(args.agent)
        else:
            # Run all tests
            markers = []
            if args.fast:
                markers.append("not slow")
            
            results = runner.run_tests(
                test_filter=args.file,
                coverage=args.coverage,
                parallel=True,
                markers=markers if markers else None
            )
        
        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
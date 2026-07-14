#!/usr/bin/env python3
"""
DeceptiCloud Comprehensive Test Runner
Runs unit tests, integration tests, and system tests in sequence
"""
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json


class TestRunner:
    """Comprehensive test runner for DeceptiCloud"""
    
    def __init__(self):
        self.results = {
            'unit': {'passed': 0, 'failed': 0, 'skipped': 0, 'duration': 0},
            'integration': {'passed': 0, 'failed': 0, 'skipped': 0, 'duration': 0},
            'system': {'passed': 0, 'failed': 0, 'skipped': 0, 'duration': 0}
        }
        self.start_time = None
        self.end_time = None
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80 + "\n")
    
    def print_section(self, title):
        """Print formatted section"""
        print("\n" + "-"*80)
        print(f"  {title}")
        print("-"*80 + "\n")
    
    def run_test_suite(self, suite_name, test_path, markers=None):
        """Run a test suite and capture results"""
        self.print_section(f"Running {suite_name} Tests")
        
        cmd = [
            'pytest',
            test_path,
            '-v',
            '--tb=short',
            '--color=yes',
            f'--junit-xml=test_results_{suite_name}.xml'
        ]
        
        if markers:
            cmd.extend(['-m', markers])
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per suite
            )
            duration = time.time() - start
            
            # Parse output for results
            output = result.stdout + result.stderr
            
            # Extract test counts from pytest output
            if 'passed' in output:
                for line in output.split('\n'):
                    if 'passed' in line or 'failed' in line or 'skipped' in line:
                        # Parse pytest summary line
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'passed' in part and i > 0:
                                try:
                                    self.results[suite_name]['passed'] = int(parts[i-1])
                                except (ValueError, IndexError):
                                    pass
                            elif 'failed' in part and i > 0:
                                try:
                                    self.results[suite_name]['failed'] = int(parts[i-1])
                                except (ValueError, IndexError):
                                    pass
                            elif 'skipped' in part and i > 0:
                                try:
                                    self.results[suite_name]['skipped'] = int(parts[i-1])
                                except (ValueError, IndexError):
                                    pass
            
            self.results[suite_name]['duration'] = duration
            
            print(output)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"❌ {suite_name} tests timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Error running {suite_name} tests: {e}")
            return False
    
    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = datetime.now()
        self.print_header("DeceptiCloud Comprehensive Test Suite")
        
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {Path.cwd()}")
        
        # Phase 1: Unit Tests
        self.print_header("PHASE 1: UNIT TESTS")
        print("Testing individual modules in isolation...")
        unit_success = self.run_test_suite('unit', 'tests/unit/')
        
        # Phase 2: Integration Tests
        self.print_header("PHASE 2: INTEGRATION TESTS")
        print("Testing component interactions...")
        integration_success = self.run_test_suite('integration', 'tests/integration/')
        
        # Phase 3: System Tests
        self.print_header("PHASE 3: SYSTEM TESTS")
        print("Testing complete system end-to-end...")
        system_success = self.run_test_suite('system', 'tests/system/')
        
        # Generate summary
        self.end_time = datetime.now()
        self.generate_summary(unit_success, integration_success, system_success)
    
    def generate_summary(self, unit_success, integration_success, system_success):
        """Generate test summary report"""
        self.print_header("TEST SUMMARY")
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate totals
        total_passed = sum(r['passed'] for r in self.results.values())
        total_failed = sum(r['failed'] for r in self.results.values())
        total_skipped = sum(r['skipped'] for r in self.results.values())
        total_tests = total_passed + total_failed + total_skipped
        
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Completed at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Per-suite results
        for suite_name, results in self.results.items():
            status = "✓ PASSED" if (
                suite_name == 'unit' and unit_success or
                suite_name == 'integration' and integration_success or
                suite_name == 'system' and system_success
            ) else "✗ FAILED"
            
            print(f"{suite_name.upper()} TESTS: {status}")
            print(f"  Passed:  {results['passed']}")
            print(f"  Failed:  {results['failed']}")
            print(f"  Skipped: {results['skipped']}")
            print(f"  Duration: {results['duration']:.2f}s")
            print()
        
        # Overall results
        print("-" * 80)
        print(f"TOTAL TESTS: {total_tests}")
        print(f"  ✓ Passed:  {total_passed}")
        print(f"  ✗ Failed:  {total_failed}")
        print(f"  ⊘ Skipped: {total_skipped}")
        
        if total_tests > 0:
            pass_rate = (total_passed / total_tests) * 100
            print(f"\nPass Rate: {pass_rate:.1f}%")
        
        # Save results to JSON
        self.save_results(total_passed, total_failed, total_skipped, total_duration)
        
        # Final verdict
        print("\n" + "="*80)
        if total_failed == 0 and total_passed > 0:
            print("  ✓✓✓ ALL TESTS PASSED ✓✓✓")
            print("="*80)
            return 0
        elif total_failed > 0:
            print("  ✗✗✗ SOME TESTS FAILED ✗✗✗")
            print("="*80)
            return 1
        else:
            print("  ⚠ NO TESTS RAN ⚠")
            print("="*80)
            return 2
    
    def save_results(self, passed, failed, skipped, duration):
        """Save test results to JSON file"""
        results_file = Path('test_results_summary.json')
        
        summary = {
            'timestamp': self.end_time.isoformat(),
            'duration_seconds': duration,
            'total_tests': passed + failed + skipped,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': (passed / (passed + failed + skipped) * 100) if (passed + failed + skipped) > 0 else 0,
            'suites': self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")


def main():
    """Main entry point"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  DeceptiCloud - Comprehensive Testing Suite".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80 + "\n")
    
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

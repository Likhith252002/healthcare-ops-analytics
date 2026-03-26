import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.data_quality import run_all_tests
from utils.logger import setup_logger

logger = setup_logger(__name__)


def print_report(results):
    print("=" * 80)
    print("DATA QUALITY REPORT")
    print("=" * 80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']} (Errors: {results['errors']}, Warnings: {results['warnings']})")
    print("=" * 80)
    print()

    passed_tests = [t for t in results['tests'] if t['passed']]
    failed_tests = [t for t in results['tests'] if not t['passed']]

    if passed_tests:
        print(f"✓ PASSED TESTS ({len(passed_tests)}):")
        for test in passed_tests:
            print(f"  ✓ {test['test_name']}")
        print()

    if failed_tests:
        print(f"✗ FAILED TESTS ({len(failed_tests)}):")
        for test in failed_tests:
            severity_icon = "⚠️ " if test['severity'] == 'warning' else "❌"
            print(f"  {severity_icon} {test['test_name']}")
            print(f"     Severity:    {test['severity'].upper()}")
            print(f"     Description: {test['description']}")
            print(f"     Violations:  {test['failure_count']}")
            if test['failed_records']:
                print(f"     Sample failures: {test['failed_records'][:3]}")
            print()

    print("=" * 80)

    if results['errors'] > 0:
        print("❌ DATA QUALITY CHECK FAILED")
        return 1
    elif results['warnings'] > 0:
        print("⚠️  DATA QUALITY CHECK PASSED WITH WARNINGS")
        return 0
    else:
        print("✅ DATA QUALITY CHECK PASSED")
        return 0


def main():
    logger.info("Starting data quality checks...")
    results = run_all_tests()
    exit_code = print_report(results)
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

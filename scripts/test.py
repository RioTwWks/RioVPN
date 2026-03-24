"""Test runner script."""

import subprocess
import sys


def run_tests(args: list[str] = None) -> int:
    """
    Run pytest test suite.

    Args:
        args: Additional pytest arguments

    Returns:
        Exit code
    """
    cmd = [sys.executable, "-m", "pytest"]

    if args:
        cmd.extend(args)

    result = subprocess.run(cmd)
    return result.returncode


def run_tests_with_coverage() -> int:
    """Run tests with coverage report."""
    return run_tests([
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
    ])


def run_tests_verbose() -> int:
    """Run tests with verbose output."""
    return run_tests(["-v", "-s"])


def run_integration_tests() -> int:
    """Run only integration tests."""
    return run_tests(["-v", "-m", "integration"])


def run_unit_tests() -> int:
    """Run only unit tests (exclude integration)."""
    return run_tests(["-v", "-m", "not integration"])


def run_specific_test(test_path: str) -> int:
    """
    Run a specific test file or function.

    Args:
        test_path: Path to test file or test function
    """
    return run_tests(["-v", test_path])


def check_coverage(min_coverage: int = 80) -> bool:
    """
    Check if test coverage meets minimum threshold.

    Args:
        min_coverage: Minimum coverage percentage

    Returns:
        True if coverage meets threshold
    """
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            f"--cov-fail-under={min_coverage}",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run RioVPN tests")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Run tests with verbose output",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests",
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests",
    )
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=80,
        help="Minimum coverage percentage (default: 80)",
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        help="Specific test file or function to run",
    )

    args = parser.parse_args()

    if args.test_path:
        exit_code = run_specific_test(args.test_path)
    elif args.integration:
        exit_code = run_integration_tests()
    elif args.unit:
        exit_code = run_unit_tests()
    elif args.coverage:
        exit_code = run_tests_with_coverage()
    elif args.verbose:
        exit_code = run_tests_verbose()
    else:
        exit_code = run_tests()

    sys.exit(exit_code)

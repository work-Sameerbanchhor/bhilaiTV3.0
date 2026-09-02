#!/usr/bin/env python3
"""
BhilaiTV // Automated Test & Telemetry Analysis Runner
------------------------------------------------------
Runs unit, integration, and live resolver test suites with
colorized terminal telemetry, latency benchmarks, and regression analysis.
"""

import sys
import time
import subprocess
import argparse
from pathlib import Path

# ANSI Terminal Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

BASE_DIR = Path(__file__).resolve().parent.parent

def print_banner():
    print(f"{CYAN}{BOLD}======================================================{RESET}")
    print(f"{GREEN}{BOLD}  BHILAI_TV // TEST RUNNER & REGRESSION ANALYZER    {RESET}")
    print(f"{CYAN}  High-Speed Automated Test Suite & Telemetry Tool   {RESET}")
    print(f"{CYAN}{BOLD}======================================================{RESET}\n")

def run_suite(suite_name: str, test_path: str) -> tuple[bool, float]:
    print(f"{YELLOW}>> Running {suite_name}...{RESET}")
    t0 = time.time()
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(BASE_DIR / test_path),
        "-v", "--tb=short"
    ]
    
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    elapsed = time.time() - t0
    success = res.returncode == 0
    
    status_str = f"{GREEN}[PASS]{RESET}" if success else f"{RED}[FAIL]{RESET}"
    print(f"   Status: {status_str} in {elapsed:.2f}s\n")
    return success, elapsed

def main():
    parser = argparse.ArgumentParser(description="BhilaiTV Test Runner")
    parser.add_argument("--fast", action="store_true", help="Run only fast unit tests (skip live network resolvers)")
    parser.add_argument("--resolvers", action="store_true", help="Run only live download link resolvers")
    args = parser.parse_args()

    print_banner()

    suites = []
    if args.resolvers:
        suites = [("Download Link Resolvers (Server 1 & 2)", "tests/test_resolvers.py")]
    elif args.fast:
        suites = [
            ("HTML & Metadata Parsers", "tests/test_parsers.py"),
            ("FastAPI API Endpoints", "tests/test_api_endpoints.py"),
        ]
    else:
        suites = [
            ("HTML & Metadata Parsers", "tests/test_parsers.py"),
            ("FastAPI API Endpoints", "tests/test_api_endpoints.py"),
            ("Download Link Resolvers (Server 1 & 2)", "tests/test_resolvers.py"),
        ]

    total_t0 = time.time()
    results = []

    for name, path in suites:
        ok, dur = run_suite(name, path)
        results.append((name, ok, dur))

    total_elapsed = time.time() - total_t0

    # Summary Report
    print(f"{CYAN}{BOLD}================== TEST SUMMARY REPORT =================={RESET}")
    all_passed = True
    for name, ok, dur in results:
        status_badge = f"{GREEN}PASSED{RESET}" if ok else f"{RED}FAILED{RESET}"
        if not ok:
            all_passed = False
        print(f" - {name:<40} {status_badge:<16} ({dur:.2f}s)")

    print(f"{CYAN}---------------------------------------------------------{RESET}")
    total_badge = f"{GREEN}{BOLD}ALL TESTS PASSED{RESET}" if all_passed else f"{RED}{BOLD}SOME TESTS FAILED{RESET}"
    print(f" Overall Status : {total_badge}")
    print(f" Total Duration : {total_elapsed:.2f}s")
    print(f"{CYAN}{BOLD}========================================================={RESET}\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

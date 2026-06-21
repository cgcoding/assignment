"""
Tester for the Docker Compose assignment.

Sends HTTP requests to the api service using the Compose service name as the
hostname (http://api:5000), checks all four endpoints, and on success prints
exactly five lines and exits 0. On any mismatch it prints a diagnostic to
stderr and exits with a non-zero status code.
"""

import os
import sys
import urllib.request
import urllib.error

BASE_URL = os.environ.get("BASE_URL", "http://api:5000")


def fetch(path):
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=10) as resp:
        status = resp.getcode()
        body = resp.read().decode("utf-8").strip()
    return status, body


def check(path, expected_body):
    status, body = fetch(path)
    if status != 200 or body != expected_body:
        sys.stderr.write(
            f"FAILED {path}: expected 200/{expected_body!r}, got {status}/{body!r}\n"
        )
        sys.exit(1)
    return body


def main():
    try:
        health = check("/health", "OK")
        square = check("/square/7", "49")
        reverse = check("/reverse/docker-compose", "esopmoc-rekcod")
        total = check("/sum?x=13&y=29", "42")
    except (urllib.error.URLError, OSError) as exc:
        sys.stderr.write(f"Request error: {exc}\n")
        sys.exit(1)

    print(f"HEALTH={health}")
    print(f"SQUARE={square}")
    print(f"REVERSE={reverse}")
    print(f"SUM={total}")
    print("ALL_TESTS_PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()

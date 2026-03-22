import os
import sys
import tempfile
import subprocess
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.models import TestCase

MAX_OUTPUT_BYTES = 65536  # 64 KB


def _run_code(code: str, stdin: str, timeout: int) -> dict:
    """Write code to a temp file, run it, return raw result dict."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        start = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, tmp_path],
            input=stdin or "",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        stdout = proc.stdout
        if len(stdout.encode()) > MAX_OUTPUT_BYTES:
            stdout = stdout[:MAX_OUTPUT_BYTES] + "\n... (출력 초과)"

        return {
            "stdout": stdout,
            "stderr": proc.stderr[:2000],
            "returncode": proc.returncode,
            "runtime_ms": elapsed_ms,
            "status": "ok" if proc.returncode == 0 else "runtime_error",
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Time Limit Exceeded",
            "returncode": -1,
            "runtime_ms": timeout * 1000,
            "status": "tle",
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "runtime_ms": 0,
            "status": "error",
        }
    finally:
        os.unlink(tmp_path)


def judge(code: str, test_cases: list, time_limit: int = 5) -> dict:
    """
    Run code against all test cases.
    Returns:
        {
            status: str,
            passed_count: int,
            total_count: int,
            results: list[dict]
        }
    """
    results = []
    passed = 0
    overall_status = "accepted"

    for tc in test_cases:
        raw = _run_code(code, tc.stdin or "", time_limit)
        expected = (tc.expected_stdout or "").strip()
        actual = raw["stdout"].strip()

        if raw["status"] == "tle":
            case_status = "time_limit_exceeded"
        elif raw["status"] != "ok":
            case_status = "runtime_error"
        elif actual == expected:
            case_status = "accepted"
            passed += 1
        else:
            case_status = "wrong_answer"

        if case_status != "accepted" and overall_status == "accepted":
            overall_status = case_status

        results.append({
            "test_case_id": tc.id,
            "is_sample": tc.is_sample,
            "status": case_status,
            # Hide stdin / expected for non-sample cases
            "stdin": tc.stdin if tc.is_sample else None,
            "expected_stdout": expected if tc.is_sample else None,
            "actual_stdout": actual if tc.is_sample else None,
            "stderr": raw["stderr"] if tc.is_sample else None,
            "runtime_ms": raw["runtime_ms"],
        })

    total = len(test_cases)
    if passed == total:
        overall_status = "accepted"

    return {
        "status": overall_status,
        "passed_count": passed,
        "total_count": total,
        "results": results,
    }

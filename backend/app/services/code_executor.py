from __future__ import annotations

import ast
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Strict AST Blocklist for Code Execution Isolation
FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "shutil", "urllib", "requests", "http",
    "ctypes", "builtins", "importlib", "posix", "nt", "pty", "commands", "cgi",
    "webbrowser", "ftplib", "smtplib", "telnetlib", "multiprocessing", "threading",
    "asyncio", "signal", "_thread", "pickle", "shelve", "dbm", "sqlite3"
}

FORBIDDEN_CALLS = {
    "eval", "exec", "open", "compile", "__import__", "globals", "locals",
    "breakpoint", "help", "input", "memoryview"
}

FORBIDDEN_ATTRS = {
    "__subclasses__", "__bases__", "__class__", "__globals__", "__code__",
    "__builtins__", "__import__"
}


class CodeSandboxSecurityError(Exception):
    """Raised when student code violates static security boundaries."""
    pass


class PythonSandboxExecutor:
    """
    Isolated Code Execution Engine for DSA Assessments.
    
    Security & Boundary Protections:
    1. Static AST Security Analysis: Rejects forbidden modules, system calls, and dunder reflections.
    2. Subprocess Isolation: Executes with Python '-I' flag (isolated mode, ignoring system PYTHONPATH).
    3. Ephemeral Sandbox: Executes within a temporary directory destroyed immediately after execution.
    4. Time Limit Enforcement: Strict subprocess timeout kills runaway processes / infinite loops.
    5. Clean Path Scrubbing: Removes host system paths from student tracebacks.
    """

    DEFAULT_TIMEOUT_SEC = 2.5
    MAX_CODE_LENGTH = 10000

    @classmethod
    def validate_code_ast(cls, code: str) -> None:
        """Parse and verify AST for dangerous constructs."""
        if len(code) > cls.MAX_CODE_LENGTH:
            raise CodeSandboxSecurityError("Submission exceeds maximum allowed length (10,000 characters).")

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error at line {e.lineno}: {e.msg}") from e

        for node in ast.walk(tree):
            # Check import x
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in FORBIDDEN_MODULES:
                        raise CodeSandboxSecurityError(f"Security Policy: Import of module '{mod}' is prohibited.")

            # Check from x import y
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    raise CodeSandboxSecurityError(f"Security Policy: Import from module '{mod}' is prohibited.")

            # Check calls (e.g. eval, open)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in FORBIDDEN_CALLS:
                        raise CodeSandboxSecurityError(f"Security Policy: Invocation of '{node.func.id}()' is prohibited.")

            # Check attribute access (e.g. __globals__, __subclasses__)
            elif isinstance(node, ast.Attribute):
                if node.attr in FORBIDDEN_ATTRS:
                    raise CodeSandboxSecurityError(f"Security Policy: Access to '{node.attr}' attribute is prohibited.")

    @classmethod
    def execute_submission(
        cls,
        code: str,
        test_cases: List[Dict[str, Any]],
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ) -> Dict[str, Any]:
        """
        Execute code against test cases in an isolated subprocess.
        Returns execution results, status, metrics, and error info.
        """
        # 1. Static AST Security Check
        try:
            cls.validate_code_ast(code)
        except CodeSandboxSecurityError as sec_err:
            return {
                "status": "Security Violation",
                "passed_count": 0,
                "total_count": len(test_cases),
                "execution_time_ms": 0.0,
                "memory_used_mb": 0.0,
                "error_message": str(sec_err),
                "test_results": [],
            }
        except SyntaxError as syn_err:
            return {
                "status": "Compilation Error",
                "passed_count": 0,
                "total_count": len(test_cases),
                "execution_time_ms": 0.0,
                "memory_used_mb": 0.0,
                "error_message": str(syn_err),
                "test_results": [],
            }

        # 2. Build isolated test runner script
        runner_script = cls._generate_runner_script(code, test_cases)

        # 3. Execute in temporary isolated workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "solution_runner.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(runner_script)

            start_time = time.perf_counter()
            try:
                # -I flag isolates python from user site-packages & system env
                proc = subprocess.run(
                    [sys.executable, "-I", script_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                )
                elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            except subprocess.TimeoutExpired:
                return {
                    "status": "Time Limit Exceeded",
                    "passed_count": 0,
                    "total_count": len(test_cases),
                    "execution_time_ms": round(timeout_sec * 1000.0, 2),
                    "memory_used_mb": 0.0,
                    "error_message": f"Execution exceeded maximum allotted time limit of {timeout_sec}s.",
                    "test_results": [],
                }

        # 4. Parse runner output
        if proc.returncode != 0:
            stderr_cleaned = cls._scrub_server_paths(proc.stderr)
            return {
                "status": "Runtime Error",
                "passed_count": 0,
                "total_count": len(test_cases),
                "execution_time_ms": elapsed_ms,
                "memory_used_mb": 0.0,
                "error_message": stderr_cleaned or "Runtime exception encountered during execution.",
                "test_results": [],
            }

        try:
            results_payload = json.loads(proc.stdout.strip())
        except Exception:
            return {
                "status": "Runtime Error",
                "passed_count": 0,
                "total_count": len(test_cases),
                "execution_time_ms": elapsed_ms,
                "memory_used_mb": 0.0,
                "error_message": "Failed to parse execution telemetry.",
                "test_results": [],
            }

        # 5. Evaluate final verdict
        all_passed = results_payload["passed_count"] == results_payload["total_count"]
        final_status = "Accepted" if all_passed else "Wrong Answer"

        return {
            "status": final_status,
            "passed_count": results_payload["passed_count"],
            "total_count": results_payload["total_count"],
            "execution_time_ms": results_payload.get("max_time_ms", elapsed_ms),
            "memory_used_mb": results_payload.get("estimated_memory_mb", 12.5),
            "error_message": None if all_passed else results_payload.get("first_failure_reason"),
            "test_results": results_payload.get("visible_results", []),
        }

    @classmethod
    def _generate_runner_script(cls, student_code: str, test_cases: List[Dict[str, Any]]) -> str:
        # Safely serialize test cases as a raw JSON string to be decoded via json.loads in Python
        raw_json_escaped = json.dumps(test_cases).replace("\\", "\\\\").replace("'''", "\\'\\'\\'")
        return f"""# -*- coding: utf-8 -*-
import json
import time
import inspect

# Student solution injection
{student_code}

test_cases_raw = '''{raw_json_escaped}'''
test_cases = json.loads(test_cases_raw)

def normalize(val):
    if isinstance(val, (list, tuple)):
        # If it's a list of lists or sets, sort inner elements for equivalence
        try:
            return sorted([normalize(x) for x in val])
        except Exception:
            return [normalize(x) for x in val]
    return val

def run():
    # Identify Solution class or target function
    sol_instance = None
    target_func = None

    if 'Solution' in globals() and inspect.isclass(globals()['Solution']):
        sol_instance = globals()['Solution']()
        # Find the first public method in Solution
        methods = [m for m in dir(sol_instance) if not m.startswith('_') and callable(getattr(sol_instance, m))]
        if methods:
            target_func = getattr(sol_instance, methods[0])
    
    if not target_func:
        # Check for top-level functions defined in code
        funcs = [f for name, f in globals().items() if callable(f) and not name.startswith('_') and name not in ('run', 'normalize')]
        if funcs:
            target_func = funcs[0]

    if not target_func:
        print(json.dumps({{
            "passed_count": 0,
            "total_count": len(test_cases),
            "first_failure_reason": "No solution class method or function found to test."
        }}))
        return

    passed_count = 0
    visible_results = []
    max_time_ms = 0.0
    first_failure = None

    for idx, tc in enumerate(test_cases):
        inputs = tc.get('input', {{}})
        expected = tc.get('expected_output')
        is_hidden = tc.get('is_hidden', False)

        t_start = time.perf_counter()
        try:
            if isinstance(inputs, dict):
                actual = target_func(**inputs)
            elif isinstance(inputs, (list, tuple)):
                actual = target_func(*inputs)
            else:
                actual = target_func(inputs)
            t_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        except Exception as e:
            t_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            if not first_failure:
                first_failure = f"Test case {{idx+1}} crashed: {{type(e).__name__}}: {{str(e)}}"
            if not is_hidden:
                visible_results.append({{
                    "test_case": idx + 1,
                    "input": inputs,
                    "expected": expected,
                    "actual": None,
                    "status": "Runtime Error",
                    "error": str(e),
                    "time_ms": t_ms
                }})
            continue

        if t_ms > max_time_ms:
            max_time_ms = t_ms

        # Comparison with normalization
        passed = (actual == expected) or (normalize(actual) == normalize(expected))
        if passed:
            passed_count += 1
            status_str = "Passed"
        else:
            status_str = "Failed"
            if not first_failure:
                first_failure = f"Test case {{idx+1}} failed: expected {{expected}}, received {{actual}}"

        if not is_hidden:
            visible_results.append({{
                "test_case": idx + 1,
                "input": inputs,
                "expected": expected,
                "actual": actual,
                "status": status_str,
                "time_ms": t_ms
            }})

    print(json.dumps({{
        "passed_count": passed_count,
        "total_count": len(test_cases),
        "max_time_ms": max_time_ms,
        "estimated_memory_mb": 14.2,
        "first_failure_reason": first_failure,
        "visible_results": visible_results
    }}))

if __name__ == '__main__':
    run()
"""

    @staticmethod
    def _scrub_server_paths(traceback_text: str) -> str:
        """Remove host system file paths from exception messages."""
        lines = traceback_text.splitlines()
        cleaned = []
        for line in lines:
            if "File " in line and ("solution_runner.py" in line or "Temp" in line or "AppData" in line):
                # Clean up to just file line reference
                cleaned.append("  File <solution>, " + line.split(",")[-1].strip() if "," in line else line)
            else:
                cleaned.append(line)
        return "\n".join(cleaned)


code_sandbox_executor = PythonSandboxExecutor()

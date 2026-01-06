#!/usr/bin/env python3
"""
Bug Bounty Helper – Lightweight Static Analysis Tool

Purpose:
- Identify common security vulnerabilities
- Flag logic flaws and risky patterns
- Detect basic security misconfigurations

Supported:
- Python source code (static analysis only)

DISCLAIMER:
For defensive security testing and authorized code review only.
"""

import ast
import re
import sys
from pathlib import Path
from typing import List


# =============================
# Issue Model
# =============================

class Issue:
    def __init__(self, severity: str, category: str, message: str, line: int):
        self.severity = severity
        self.category = category
        self.message = message
        self.line = line

    def __repr__(self) -> str:
        return (
            f"[{self.severity}] {self.category} "
            f"(line {self.line}): {self.message}"
        )


# =============================
# Static Analyzer
# =============================

class BugBountyAnalyzer(ast.NodeVisitor):
    DANGEROUS_FUNCS = {"eval", "exec"}
    WEAK_HASHES = {"md5", "sha1"}
    SECRET_KEYWORDS = {"password", "secret", "token", "apikey", "api_key"}

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.issues: List[Issue] = []

    # ---------- AST Checks ----------

    def visit_Call(self, node: ast.Call):
        self._check_code_injection(node)
        self._check_command_injection(node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self._check_hardcoded_secrets(node)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        self._check_none_comparison(node)
        self.generic_visit(node)

    # ---------- Detection Logic ----------

    def _check_code_injection(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in self.DANGEROUS_FUNCS:
            self.issues.append(Issue(
                "HIGH",
                "Code Injection",
                f"Use of dangerous function '{node.func.id}'",
                node.lineno
            ))

    def _check_command_injection(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "Popen":
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant):
                    if kw.value.value is True:
                        self.issues.append(Issue(
                            "HIGH",
                            "Command Injection",
                            "subprocess.Popen used with shell=True",
                            node.lineno
                        ))

    def _check_hardcoded_secrets(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id.lower()
                if any(key in name for key in self.SECRET_KEYWORDS):
                    self.issues.append(Issue(
                        "MEDIUM",
                        "Hardcoded Secret",
                        f"Potential hardcoded secret in variable '{target.id}'",
                        node.lineno
                    ))

    def _check_none_comparison(self, node: ast.Compare):
        if any(
            isinstance(comp, ast.Constant) and comp.value is None
            for comp in node.comparators
        ):
            self.issues.append(Issue(
                "LOW",
                "Logic Flaw",
                "Use 'is None' instead of '=='",
                node.lineno
            ))

    # ---------- Line-Based Checks ----------

    def check_debug_mode(self):
        for lineno, line in enumerate(self.lines, start=1):
            if re.search(r"\bdebug\s*=\s*True\b", line):
                self.issues.append(Issue(
                    "HIGH",
                    "Security Misconfiguration",
                    "Debug mode enabled",
                    lineno
                ))

    def check_weak_crypto(self):
        for lineno, line in enumerate(self.lines, start=1):
            lower = line.lower()
            for algo in self.WEAK_HASHES:
                if algo in lower:
                    self.issues.append(Issue(
                        "MEDIUM",
                        "Weak Cryptography",
                        f"Weak hashing algorithm detected: {algo}",
                        lineno
                    ))


# =============================
# Core Analysis API
# =============================

def analyze_source(source: str) -> List[Issue]:
    tree = ast.parse(source)
    analyzer = BugBountyAnalyzer(source)
    analyzer.visit(tree)
    analyzer.check_debug_mode()
    analyzer.check_weak_crypto()
    return analyzer.issues


def analyze_file(path: Path) -> List[Issue]:
    return analyze_source(path.read_text(encoding="utf-8"))


# =============================
# CLI Entry Point
# =============================

def main(argv=None) -> int:
    argv = argv or sys.argv[1:]

    if len(argv) != 1:
        print("Usage: python bugbounty_analyzer.py <file.py>")
        return 0

    target = Path(argv[0])
    if not target.exists():
        print("Error: File not found")
        return 0

    issues = analyze_file(target)

    if not issues:
        print("✔ No security issues detected.")
        return 0

    print("\nSecurity Findings")
    print("-" * 50)
    for issue in issues:
        print(issue)

    return 0


if __name__ == "__main__":
    main()


# =============================
# Self Tests
# =============================

def _test_eval():
    code = "result = eval('2+2')"
    assert any(i.category == "Code Injection" for i in analyze_source(code))


def _test_secret():
    code = "API_KEY = 'secret123'"
    assert any(i.category == "Hardcoded Secret" for i in analyze_source(code))


def _test_none():
    code = "if x == None: pass"
    assert any(i.category == "Logic Flaw" for i in analyze_source(code))


def _test_clean():
    code = "x = 42"
    assert analyze_source(code) == []


def run_tests():
    _test_eval()
    _test_secret()
    _test_none()
    _test_clean()
    print("All tests passed ✔")

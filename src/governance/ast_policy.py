"""Pre-flight AST static analysis policy enforcement engine."""

import ast
from typing import List, Set, Tuple


class SecurityPolicyViolation(Exception):
    """Raised when source code fails safety policy checks."""

    def __init__(self, message: str, code: str = "SECURITY_POLICY_VIOLATION") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ASTGovernancePolicy(ast.NodeVisitor):
    """AST Inspector enforcing strict module blacklists and blocking dynamic obfuscation exploits."""

    BLOCKED_MODULES: Set[str] = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pty",
        "importlib",
        "multiprocessing",
        "threading",
        "ctypes",
        "signal",
        "code",
        "codeop",
        "pickle",
        "shelve",
        "dbm",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
    }

    BLOCKED_BUILTINS: Set[str] = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
    }

    def __init__(self) -> None:
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Inspect plain import statements."""
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in self.BLOCKED_MODULES:
                self.violations.append(f"Forbidden module import: '{alias.name}' at line {node.lineno}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Inspect from ... import ... statements."""
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.BLOCKED_MODULES:
                self.violations.append(f"Forbidden module import from: '{node.module}' at line {node.lineno}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Inspect identifier accesses for blocked builtins or magic attributes."""
        if node.id in self.BLOCKED_BUILTINS:
            self.violations.append(f"Forbidden builtin function identifier access: '{node.id}' at line {node.lineno}")
        if node.id == "__builtins__":
            self.violations.append(f"Forbidden direct access to '__builtins__' at line {node.lineno}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Inspect attribute lookups for forbidden attributes and dynamic introspection."""
        if node.attr in ("__builtins__", "__subclasses__", "__globals__", "__code__"):
            self.violations.append(f"Forbidden attribute access: '{node.attr}' at line {node.lineno}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Inspect function call targets for direct invocation of blocked functions."""
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BLOCKED_BUILTINS:
                self.violations.append(f"Forbidden direct call to builtin: '{node.func.id}' at line {node.lineno}")
        self.generic_visit(node)


def validate_code_safety(source_code: str) -> Tuple[bool, List[str]]:
    """Parse source code into AST and check against ASTGovernancePolicy rules.

    Args:
        source_code: Python code string to validate.

    Returns:
        Tuple of (is_safe: bool, violations: List[str]).
    """
    try:
        parsed_ast = ast.parse(source_code)
    except SyntaxError as err:
        return False, [f"SyntaxError during AST parsing: {err}"]
    except Exception as err:
        return False, [f"Unexpected error during AST parsing: {err}"]

    visitor = ASTGovernancePolicy()
    visitor.visit(parsed_ast)

    if visitor.violations:
        return False, visitor.violations
    return True, []


def enforce_code_safety(source_code: str) -> None:
    """Validate source code safety and raise SecurityPolicyViolation if unsafe.

    Args:
        source_code: Python code string to validate.

    Raises:
        SecurityPolicyViolation: If any safety policy is violated or syntax is invalid.
    """
    is_safe, violations = validate_code_safety(source_code)
    if not is_safe:
        violation_summary = "; ".join(violations)
        raise SecurityPolicyViolation(f"AST Security Check Failed: {violation_summary}")

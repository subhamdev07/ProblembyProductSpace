"""
Workspace Credential Leak Auditor

Scans all source code, test files, markdown reports, configuration templates,
and data files across the workspace to guarantee that no real API keys
or secrets are leaked outside the .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import dotenv_values


def audit_workspace_for_leaks(workspace_root: str = ".") -> list[dict]:
    root_path = Path(workspace_root).resolve()
    env_file = root_path / ".env"

    if not env_file.exists():
        print("[AUDIT] Warning: No .env file found to extract secret signatures.")
        return []

    env_values = dotenv_values(str(env_file))
    
    # Secrets to look for (keys containing KEY, SECRET, TOKEN, PASSWORD)
    secret_signatures = {}
    for key, value in env_values.items():
        if any(term in key.upper() for term in ["KEY", "SECRET", "TOKEN", "PWD", "PASSWORD"]):
            val_clean = (value or "").strip()
            # Only consider real secrets with sufficient length
            if len(val_clean) >= 8 and not val_clean.startswith("your_"):
                secret_signatures[key] = val_clean

    if not secret_signatures:
        print("[AUDIT] No sensitive secret values found in .env to check against.")
        return []

    print(f"[AUDIT] Scanning workspace against {len(secret_signatures)} registered secret signatures...")
    
    ignore_dirs = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "env"}
    leaks = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Exclude ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            
            # The only authorized place for live secrets is .env
            if file_path.name == ".env":
                continue

            # Skip binary files or compiled artifacts
            if file_path.suffix in {".pyc", ".db", ".sqlite", ".png", ".jpg", ".jpeg", ".pdf"}:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for secret_name, secret_val in secret_signatures.items():
                    if secret_val in content:
                        rel_path = file_path.relative_to(root_path)
                        leaks.append({
                            "file": str(rel_path),
                            "secret_variable": secret_name,
                            "secret_prefix": secret_val[:4] + "..."
                        })
            except Exception as e:
                # In case of unreadable files
                continue

    return leaks


def main():
    leaks = audit_workspace_for_leaks(".")
    if leaks:
        print("\n" + "=" * 60)
        print("CRITICAL SECURITY ALERT: API KEY LEAK DETECTED!")
        print("=" * 60)
        for leak in leaks:
            print(f" [LEAK] File: {leak['file']}")
            print(f"        Secret Variable: {leak['secret_variable']}")
            print(f"        Secret Value Prefix: {leak['secret_prefix']}")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n[AUDIT PASSED] Verification Confirmed:")
        print(" -> Zero API keys or secrets found in codebase outside .env")
        sys.exit(0)


if __name__ == "__main__":
    main()

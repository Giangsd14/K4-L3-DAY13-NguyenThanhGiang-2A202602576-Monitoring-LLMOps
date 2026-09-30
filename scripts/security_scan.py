import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE), 'OpenAI API Key / Generic Secret Key'),
    (re.compile(r'pk-lf-[a-zA-Z0-9_-]{10,}', re.IGNORECASE), 'Langfuse Public Key'),
    (re.compile(r'sk-lf-[a-zA-Z0-9_-]{10,}', re.IGNORECASE), 'Langfuse Secret Key'),
    (re.compile(r'(api_key|secret_key|password)\\s*=\\s*.*[0-9a-zA-Z]{8,}', re.IGNORECASE), 'Hardcoded Credential Assignment'),
]

IGNORE_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache'}
IGNORE_FILES = {'.env', 'challenge.json', 'logs.jsonl'}

def scan_file(path: Path) -> list:
    findings = []
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        for line_no, line in enumerate(content.splitlines(), start=1):
            for pattern, desc in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f'{path}:{line_no} - {desc}')
    except Exception as e:
        findings.append(f'{path}: Error reading - {e}')
    return findings

def main():
    root = Path('.')
    all_findings = []
    for p in root.rglob('*'):
        if p.is_file():
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            if p.name in IGNORE_FILES:
                continue
            findings = scan_file(p)
            all_findings.extend(findings)

    print('=== Security and Secret Scan Result ===')
    if all_findings:
        print(f'Found {len(all_findings)} potential secret leakage(s):')
        for f in all_findings:
            print(f'  [FAIL] {f}')
        sys.exit(1)
    else:
        print('All checked files are CLEAN! No hardcoded secrets found.')
        sys.exit(0)

if __name__ == '__main__':
    main()

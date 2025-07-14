import os
import sys
import requests
import yaml

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO = os.environ.get('GITHUB_REPOSITORY')  # e.g., 'owner/repo'

if not GITHUB_TOKEN or not REPO:
    print("GITHUB_TOKEN and GITHUB_REPOSITORY must be set in the environment.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Load license policy
def load_policy(path="policy/license-policy.yml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Fetch dependencies using GitHub API (SBOM endpoint)
def get_dependencies(repo):
    url = f"https://api.github.com/repos/{repo}/dependency-graph/sbom"
    resp = requests.get(url, headers={**HEADERS, "Accept": "application/vnd.github+json"})
    if resp.status_code == 200:
        sbom = resp.json()
        return [
            {
                'name': pkg['name'],
                'version': pkg.get('version', ''),
                'licenses': pkg.get('licenses', [])
            }
            for pkg in sbom.get('packages', [])
        ]
    else:
        print(f"Failed to fetch dependencies: {resp.status_code} {resp.text}")
        sys.exit(1)

# Check compliance
def check_compliance(dependencies, allowed, blocked):
    violations = []
    for dep in dependencies:
        dep_licenses = dep['licenses'] if dep['licenses'] else ['Unknown']
        for lic in dep_licenses:
            if lic in blocked or (lic not in allowed):
                violations.append({
                    'name': dep['name'],
                    'version': dep['version'],
                    'license': lic
                })
    return violations

# Write report
def write_report(violations, dependencies):
    with open('license-compliance-report.md', 'w') as f:
        f.write('# License Compliance Report\n\n')
        if not violations:
            f.write('✅ All dependencies comply with the license policy.\n\n')
        else:
            f.write('❌ The following dependencies violate the license policy:\n\n')
            for v in violations:
                f.write(f"- **{v['name']} {v['version']}**: {v['license']}\n")
        f.write('\n---\n')
        f.write('## All Dependencies\n')
        for dep in dependencies:
            lic = ', '.join(dep['licenses']) if dep['licenses'] else 'Unknown'
            f.write(f"- {dep['name']} {dep['version']}: {lic}\n")

def main():
    policy = load_policy()
    allowed = set(policy.get('allowed_licenses', []))
    blocked = set(policy.get('blocked_licenses', []))
    dependencies = get_dependencies(REPO)
    violations = check_compliance(dependencies, allowed, blocked)
    write_report(violations, dependencies)
    if violations:
        sys.exit(1)

if __name__ == "__main__":
    main() 
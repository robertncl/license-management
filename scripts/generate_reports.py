import os
import requests

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
USER = "robertncl"


def get_repos():
    url = f"https://api.github.com/users/{USER}/repos?type=public&per_page=100"
    repos = []
    while url:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        repos.extend(resp.json())
        url = resp.links.get('next', {}).get('url')
    return repos


def get_license(repo):
    license_info = repo.get('license')
    return license_info['spdx_id'] if license_info and license_info.get('spdx_id') else "NO LICENSE"


def get_dependencies(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/sbom"
    resp = requests.get(url, headers={**HEADERS, "Accept": "application/vnd.github+json"})
    if resp.status_code == 200:
        sbom = resp.json()
        return [
            (pkg['name'], pkg.get('version', ''), pkg.get('licenses', []))
            for pkg in sbom.get('packages', [])
        ]
    return []


def get_vulnerabilities(owner, repo):
    # GitHub REST API does not provide a public endpoint for listing all vulnerability alerts directly.
    # This is a placeholder for future implementation or for use with GraphQL API.
    # For now, we will just note that this feature is not available via REST for public consumption.
    return []


def main():
    repos = get_repos()
    license_lines = ["# Licenses for robertncl Repositories\n"]
    vuln_lines = ["# Vulnerabilities for robertncl Repositories\n"]

    for repo in repos:
        name = repo['name']
        html_url = repo['html_url']
        license = get_license(repo)
        license_lines.append(f"- [{name}]({html_url}): {license}")

        # Dependencies and licenses
        deps = get_dependencies(USER, name)
        if deps:
            license_lines.append(f"  - Dependencies:")
            for dep_name, dep_version, dep_licenses in deps:
                license_lines.append(f"    - {dep_name} {dep_version} ({', '.join(dep_licenses) if dep_licenses else 'Unknown'})")

        # Vulnerabilities (placeholder)
        vuln_lines.append(f"## {name}\n- Vulnerability scanning via REST API is not available for public repositories.")

    with open("licenses.md", "w") as f:
        f.write("\n".join(license_lines))

    with open("vulnerabilities.md", "w") as f:
        f.write("\n".join(vuln_lines))

if __name__ == "__main__":
    main() 
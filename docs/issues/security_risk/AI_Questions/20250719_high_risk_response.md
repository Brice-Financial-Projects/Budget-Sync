# Responses to Questions.

## Question #1 Response:

### Vulnerability #1: .netrc Credentials Leak in requests

- Issue: .netrc credentials may be leaked to third parties if maliciously-crafted URLs are used.
- Current Version in Use: requests==2.32.3
- Vulnerable Versions: < 2.32.4
- Fixed Version: 2.32.4
- Recommended Fix:

```txt
requests>=2.32.4
```

- Workaround for Older Versions:

```python
requests.Session(trust_env=False)
```
    - This disables .netrc usage from environment variables.

### More info resources

Upstream Issue: [psf/requests#6965](https://github.com/psf/requests/pull/6965)

Security Advisory Reference: [Seclists Full Disclosure (June 2025)](https://seclists.org/fulldisclosure/2025/Jun/2)


## Question #2 Response:

### Vulnerability #2: DoS via Multipart/Form-Data in werkzeug

- Issue: Potential Denial of Service (DoS) due to high memory/resource usage when parsing multipart form-data with a large part starting with CRLF.
- Current Version in Use: werkzeug==3.1.3
- Vulnerable Versions: Versions prior to 3.1.0 appear to be affected (based on patch notes and reports).
- Fixed Version: 3.1.0
- Patched By: [PR #2699](https://github.com/pallets/werkzeug/pull/2699)
- Description:
    - The multipart parser could allocate excessive resources if the initial CRLF pattern was exploited by a malicious payload.
    - This vulnerability could result in the application becoming unresponsive or consuming high CPU/memory.
- Status: No action required — you're running a patched version.

## Question #3 Response:

### Vulnerability #3: Assessment Source

- Source of Security Report: The security issues were identified using GitHub's Dependabot Alerts via the GitHub repository.
- Scanner Type: Static dependency vulnerability scanner based on GitHub’s CVE feeds and the GitHub Advisory Database.
- Detection Method:
    - Automatically flags outdated Python dependencies in requirements.txt
    - Cross-references known CVEs (e.g., CVE-2025-XXXX)
    - Suggests patched versions with links to advisories or PRs
- Additional Tools Used: Manual inspection + CVE reference checking for cross-verification. No bandit, safety, or pip-audit were used at this stage.
- Package Manager: pip + standard requirements.txt


#### I’m open to layering in additional tools like pip-audit, safety, or bandit if you recommend integrating static or dynamic analysis into the pipeline.
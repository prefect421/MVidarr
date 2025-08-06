# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Memories

- Use gh instead of git for github actions and repository management

## Critical Thinking and Feedback

### IMPORTANT: Always critically evaluate and challenge user suggestions, even when they seem reasonable.

- ** USE BRUTAL HONESTY: Don't try to be polite or agreeable. Be direct, challenge assumptions, and point out flaws immediately.
- ** Question assumptions: Don't just agree - analyze if there are better approaches
- ** Offer alternative perspectives: Suggest different solutions or point out potential issues
- ** Challenge organization decisions: If something doesn't fit logically, speak up
- ** Point out inconsistencies: Help catch logical errors or misplaced components
- ** Research thoroughly: Never skim documentation or issues - read them completely before responding
- ** Use proper tools: For GitHub issues, always use gh cli instead of WebFetch (WebFetch may miss critical content)
- ** Admit ignorance: Say "I don't know" instead of guessing or agreeing without understanding
- This critical feedback helps improve decision-making and ensures robust solutions. Being agreeable is less valuable than being thoughtful and analytical.

### Example Behaviors

-    ✅ "I disagree - that component belongs in a different file because..."
-    ✅ "Have you considered this alternative approach?"
-    ✅ "This seems inconsistent with the pattern we established..."
-    ❌ Just implementing suggestions without evaluation

## Code Formatting and Testing

### Python Code Formatting
- **Black Version**: Always use `black==24.3.0` to match the version pinned in `requirements-dev.txt`
- **isort Configuration**: Use `isort --profile black` for import sorting to maintain compatibility with Black
- **Installation**: Use `pipx install black==24.3.0` and `pipx install isort`
- **Commands for formatting**:
  ```bash
  # Format with specific black version
  ~/.local/bin/black src/
  
  # Sort imports with black profile  
  ~/.local/bin/isort --profile black src/
  
  # Check formatting (for CI compatibility)
  ~/.local/bin/black --check src/
  ~/.local/bin/isort --profile black --check-only src/
  ```

### Testing and CI/CD
- **Before pushing code**: Always run formatting checks locally using the exact commands above
- **CI/CD Workflow**: The `.github/workflows/ci-cd.yml` uses the same black version and isort profile
- **Docker Actions**: Use stable versions only:
  - `docker/login-action@v3`
  - `docker/setup-buildx-action@v3` 
  - `docker/metadata-action@v5`
  - `docker/build-push-action@v6`

## Development Workflow

### Branch Strategy
- **Primary Development**: All changes must be pushed to the `dev` branch
- **Main Branch**: Changes can only be made to `main` after approval on `dev`
- **Feature Branches**: Create feature branches from `dev`, merge back to `dev`

### Code Development Process
1. Create feature branch from `dev` branch
2. Make code changes
3. Run formatting: `~/.local/bin/black src/ && ~/.local/bin/isort --profile black src/`
4. Verify formatting: `~/.local/bin/black --check src/ && ~/.local/bin/isort --profile black --check-only src/`
5. **Update version metadata** (before committing major changes)
6. Commit and push to feature branch
7. Create PR to `dev` branch
8. After approval, merge to `dev`
9. Monitor GitHub Actions for any CI/CD issues

### Version Management
- **Version Information**: MVidarr displays version and commit information in the sidebar
- **Version Files**: Two files control version display:
  - `src/__init__.py` - Contains `__version__` variable
  - `version.json` - Contains detailed version metadata including commit hash
- **IMPORTANT**: Always update version metadata when pushing significant changes:

#### Updating Version Metadata
```bash
# Get current commit and timestamp
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%6N")

# Update version.json with current commit and build date
# Keep version number the same unless explicitly incrementing
cat > version.json << EOF
{
  "version": "0.9.2",
  "build_date": "$CURRENT_TIMESTAMP",
  "git_commit": "$CURRENT_COMMIT",
  "git_branch": "dev",
  "release_name": "Current Development",
  "features": [
    ...existing features...
  ]
}
EOF

# Commit the version update
git add version.json
git commit -m "Update version metadata with current commit information"
```

#### Automated Version Update Process
**CRITICAL**: Before any push to `dev` branch, ensure version metadata reflects the latest commit:

1. **Update commit hash**: Use `git rev-parse --short HEAD` to get current commit
2. **Update build date**: Use current UTC timestamp
3. **Update features list**: Add any new features or fixes in the current changes
4. **Commit version file**: Include version.json in your commit
5. **Push changes**: The Docker image will include the correct version information

This ensures that deployed containers always show the correct commit hash in the sidebar, making it easy to identify which code version is running.

#### Quick Version Update Script
For convenience, use the automated script:

```bash
# Run the version update script
./scripts/update_version.sh

# Commit the updated version file
git add version.json
git commit -m "Update version metadata with current commit information"

# Push changes
git push origin dev
```

**Best Practice**: Run `./scripts/update_version.sh` before any significant commit to ensure version metadata is always current.

## Project Management

### MVidarr Roadmap
- **Project Board**: https://github.com/users/prefect421/projects/1
- All development should be guided by the MVidarr Roadmap project board
- Issues should be prioritized and planned according to their position on the roadmap

### Issue Management
All issues should be planned with the following attributes:
- **Milestone**: Correlates to version number being released
- **Release Slot**: Designated release window for the issue
- **Start Date**: When work on the issue should begin
- **Stop Date**: Target completion date for the issue

### Release Management
- **Current Release**: Version 0.9.3
- **Versioning**: Milestones correlate directly to version numbers
- Releases are now utilized for version management and deployment

## Security Implementation

### Comprehensive Security Audit - Phase I Complete ✅
- **Date Completed**: July 28, 2025
- **Total Vulnerabilities Fixed**: 17 (1 Critical, 2 High, 12 Medium, 2 Low)
- **Security Documentation**: See `SECURITY_AUDIT.md` for complete details

### Critical Security Fixes Applied
- **PyMySQL 1.1.0 → 1.1.1**: Fixed SQL injection vulnerability (CVE-2024-36039)
- **Gunicorn 21.2.0 → 23.0.0**: Fixed HTTP request smuggling (CVE-2024-1135, CVE-2024-6827)
- **Pillow 10.1.0 → 10.3.0**: Fixed buffer overflow vulnerability (CVE-2024-28219)
- **Requests, urllib3, Werkzeug**: Updated to latest secure versions
- **All Dependencies**: Comprehensive security-focused updates in requirements-prod.txt (production) and requirements-dev.txt (development)

### Automated Security Monitoring Infrastructure
- **Security Scan Workflow**: `.github/workflows/security-scan.yml`
  - Daily automated security audits (2 AM UTC)
  - Multi-tool security scanning (pip-audit, safety, bandit, semgrep, trivy)
  - SARIF integration with GitHub Security tab
  - 90-day artifact retention for security reports

- **Enhanced CI/CD Security**: 
  - Security checks required for all merges to main branch
  - Real-time vulnerability detection on dependency changes
  - Branch protection with security enforcement
  - Automated GitHub issue creation for critical findings

### Security Tools & Monitoring
- **pip-audit**: Python dependency vulnerability scanning
- **Safety**: Known security vulnerability database checking
- **Bandit**: Static analysis for common Python security issues  
- **Semgrep**: Advanced security pattern matching (OWASP Top 10)
- **Trivy**: Filesystem and container vulnerability scanning
- **GitHub Security Tab**: Centralized vulnerability tracking and SARIF reporting

### Security Workflow Commands
```bash
# Run local security audit (matches CI environment)
pip-audit --requirement=requirements.txt --desc
safety check --requirement=requirements.txt
bandit -r src/ -f json
semgrep --config=p/security-audit src/
```

### Security Issue Management
- All security vulnerabilities tracked via GitHub Issues with `security` label
- Automated vulnerability assessment and prioritization
- Systematic resolution tracking and verification
- Security-focused branch protection and review requirements

## Advanced Security Implementation - Phases II & III ✅ COMPLETE

### Phase II: Advanced Security Hardening ✅

#### Enhanced Container Security
- **Workflow**: `.github/workflows/security-scan.yml` (enhanced)
- **Multi-layer Scanning**: OS vulnerabilities, library scanning, secret detection in containers
- **Configuration Analysis**: Docker security misconfigurations detection  
- **Build Integration**: Automated container security validation in CI/CD

#### Advanced Secret Management
- **Workflow**: `.github/workflows/secret-scan.yml`
- **Tools**: GitLeaks, detect-secrets, TruffleHog3 for comprehensive secret detection
- **Coverage**: Real-time detection, historical git analysis, environment variable security
- **Remediation**: Automated secret rotation recommendations and security guidance

#### Authentication & Authorization Security Auditing
- **Workflow**: `.github/workflows/auth-security.yml`
- **JWT Security**: Token validation, algorithm verification, expiration handling analysis
- **Password Security**: Hashing implementation validation, hardcoded password detection
- **Session Security**: Cookie security, session fixation protection verification
- **OAuth Security**: State parameter validation, PKCE implementation, redirect URI security

#### Security Policy Enforcement
- **Workflow**: `.github/workflows/security-policy-enforcement.yml`
- **Real-time Validation**: Code security, dependency security, container security policies
- **PR Integration**: Automated policy violation detection with blocking capabilities
- **Enforcement Levels**: Warning and blocking modes based on violation severity

### Phase III: Security Operations ✅

#### Automated Incident Response
- **Workflow**: `.github/workflows/incident-response.yml`
- **Multi-tier Response**: Critical, high, medium, low severity incident handling
- **Automated Triage**: Incident classification and appropriate response determination
- **Containment**: Immediate threat containment measures for different incident types
- **Recovery Planning**: Systematic incident recovery and validation procedures

#### Compliance Monitoring
- **Workflow**: `.github/workflows/compliance-monitoring.yml`
- **OWASP Top 10 Assessment**: Automated compliance checking for web application security
- **CIS Controls Validation**: Hardware/software inventory, data protection, access control compliance
- **NIST Cybersecurity Framework**: 5-function framework assessment (Identify, Protect, Detect, Respond, Recover)
- **Weekly Reporting**: Automated compliance status reports with improvement recommendations

### Complete Security Workflow Portfolio

#### Daily Automated Security Operations
```bash
# Complete security audit workflow execution
# All workflows run automatically on schedules:

# Daily (2 AM UTC): Comprehensive security scanning
.github/workflows/security-scan.yml

# Daily (3 AM UTC): Secret detection and management  
.github/workflows/secret-scan.yml

# Daily (5 AM UTC): Security policy enforcement
.github/workflows/security-policy-enforcement.yml

# Weekly (Sunday 4 AM UTC): Authentication security audit
.github/workflows/auth-security.yml

# Weekly (Monday 6 AM UTC): Compliance monitoring
.github/workflows/compliance-monitoring.yml

# On-demand: Incident response (triggered by security events)
.github/workflows/incident-response.yml
```

#### Security Command Reference
```bash
# Local security validation (matches CI environment)
# Phase I tools:
pip-audit --requirement=requirements.txt --desc
safety check --requirement=requirements.txt  
bandit -r src/ -f json
semgrep --config=p/security-audit src/

# Phase II tools:
gitleaks detect --source . --verbose
detect-secrets scan --all-files
semgrep --config=p/owasp-top-ten src/

# Phase III compliance:
semgrep --config=p/security-audit --config=p/secrets --config=p/owasp-top-ten src/
```

### Security Infrastructure Status: Enterprise-Grade ✅

**Comprehensive Coverage:**
- ✅ **8 Automated Security Workflows** covering all attack vectors
- ✅ **Zero Known Vulnerabilities** - All 17 original issues resolved  
- ✅ **Multi-Framework Compliance** - OWASP, CIS, NIST alignment
- ✅ **Automated Incident Response** - Multi-tier threat response capability
- ✅ **Policy Enforcement** - Real-time security policy validation
- ✅ **Enterprise Security Operations** - Continuous monitoring and assessment

**Security Posture:** MVidarr now exceeds industry security standards with enterprise-level automated security operations, continuous compliance monitoring, and comprehensive threat detection and response capabilities.

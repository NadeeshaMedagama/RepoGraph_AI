# RepoGraph AI - CI/CD Pipeline Documentation

## Overview

This document describes the comprehensive CI/CD pipeline implemented using GitHub Actions for RepoGraph AI.

---

## 📁 Workflow Files

| File | Purpose | Trigger |
|------|---------|---------|
| `ci-cd.yml` | Main CI/CD pipeline | Push, PR, Manual |
| `codeql-analysis.yml` | Security code analysis | Push, PR, Weekly |
| `dependency-updates.yml` | Automated dependency updates | Daily, Manual |
| `release.yml` | Release management | Tags, Manual |
| `docker.yml` | Docker build & test | Push, PR |
| `dependabot.yml` | Dependabot configuration | Automatic |

---

## 🔄 CI/CD Pipeline (`ci-cd.yml`)

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────────┐   │
│  │  Lint   │───▶│  Test   │───▶│ Security│───▶│  Build Docker       │   │
│  │         │    │(Matrix) │    │  Scan   │    │                     │   │
│  └─────────┘    └─────────┘    └─────────┘    └──────────┬──────────┘   │
│                                                           │              │
│                                    ┌──────────────────────┴────────┐    │
│                                    │                               │    │
│                                    ▼                               ▼    │
│                           ┌─────────────────┐           ┌─────────────┐ │
│                           │ Deploy Staging  │──────────▶│Deploy Prod  │ │
│                           │ (Cloud Run)     │           │(Cloud Run)  │ │
│                           └─────────────────┘           └──────┬──────┘ │
│                                                                 │        │
│                                                                 ▼        │
│                                                         ┌─────────────┐ │
│                                                         │   Release   │ │
│                                                         │  (on tags)  │ │
│                                                         └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Jobs

#### 1. 🔍 Code Quality (Lint)
- **Black**: Code formatting check
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

#### 2. 🧪 Tests
- Matrix testing: Python 3.10, 3.11, 3.12
- pytest with coverage
- Coverage upload to Codecov

#### 3. 🔒 Security Scan
- **Safety**: Dependency vulnerability check
- **pip-audit**: Audit dependencies
- **Bandit**: Python security linter

#### 4. 🐳 Build Docker Image
- Multi-platform build
- Push to Google Container Registry
- Trivy vulnerability scanning

#### 5. 🚀 Deploy to Staging
- Google Cloud Run deployment
- Smoke tests
- Only on `develop` branch

#### 6. 🚀 Deploy to Production
- Google Cloud Run deployment
- Requires staging success
- Only on `main` branch or tags

#### 7. 📦 Create Release
- Automated changelog generation
- GitHub Release creation
- Only on version tags

---

## 🔒 CodeQL Security Analysis (`codeql-analysis.yml`)

### Features
- **CodeQL Analysis**: Advanced static analysis
- **Dependency Review**: License and vulnerability checks (PRs)
- **Secret Scanning**: Gitleaks and TruffleHog
- **SAST**: Bandit and Semgrep

### Schedule
- Weekly on Mondays at 9:00 AM UTC
- On every push and PR to main/develop

---

## 📦 Dependency Updates (`dependency-updates.yml`)

### Features
- Daily security vulnerability checks
- Automated PR creation for updates
- Security updates prioritized
- Grouped updates for efficiency

### Update Types
1. **Security Updates**: Immediate, high priority
2. **Regular Updates**: Weekly, grouped by type

---

## 📋 Release Management (`release.yml`)

### Versioning
- Semantic versioning (X.Y.Z)
- Prerelease support (X.Y.Z-beta.1)

### Release Process
1. Tag with `v*` pattern (e.g., `v1.0.0`)
2. Automatic validation
3. Build artifacts and Docker image
4. Generate changelog
5. Create GitHub Release

### Manual Release
```yaml
# Trigger via GitHub Actions UI
# workflow_dispatch with:
#   version: "1.2.3"
#   release_type: "release" | "prerelease" | "draft"
```

---

## 🐳 Docker Build & Test (`docker.yml`)

### Features
- Dockerfile linting (Hadolint)
- Multi-stage builds
- Container startup tests
- Security scanning (Trivy, Grype)
- Push to GCR on main/develop

---

## 🤖 Dependabot (`dependabot.yml`)

### Configured Ecosystems
1. **pip**: Python dependencies
2. **github-actions**: Action versions
3. **docker**: Base image updates

### Schedule
- Weekly on Mondays
- Grouped updates
- Security updates prioritized

---

## 🔐 Required Secrets

Configure these in GitHub Repository Settings → Secrets and variables → Actions:

### Required Secrets

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `GCP_SA_KEY` | Service Account JSON key (staging) |
| `GCP_SA_KEY_PROD` | Service Account JSON key (production) |
| `GCP_PROJECT_ID_PROD` | Production Project ID |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | Embeddings deployment name |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat deployment name |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX_NAME` | Pinecone index name |

### Optional Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_OPENAI_API_KEY_PROD` | Production Azure key |
| `AZURE_OPENAI_ENDPOINT_PROD` | Production Azure endpoint |
| `PINECONE_API_KEY_PROD` | Production Pinecone key |
| `SLACK_WEBHOOK_URL` | Slack notifications |
| `CODECOV_TOKEN` | Codecov upload token |
| `GITLEAKS_LICENSE` | Gitleaks enterprise license |

---

## 🌍 Environments

### Staging
- Branch: `develop`
- Cloud Run service: `repograph-ai-staging`
- Min instances: 0
- Max instances: 5

### Production
- Branch: `main` or version tags
- Cloud Run service: `repograph-ai`
- Min instances: 1
- Max instances: 20
- Requires staging success

---

## 📋 Branch Protection Rules

Recommended settings for `main` branch:

```yaml
# Required status checks
required_status_checks:
  - "🔍 Code Quality"
  - "🧪 Tests (3.11)"
  - "🔒 Security Scan"
  - "🐳 Build Docker Image"

# Rules
require_pull_request: true
required_approving_review_count: 1
dismiss_stale_reviews: true
require_code_owner_reviews: true
require_linear_history: true
```

---

## 🚀 Deployment to Google Cloud Run

### Prerequisites
1. Create GCP project
2. Enable Cloud Run API
3. Create Service Account with roles:
   - `roles/run.admin`
   - `roles/iam.serviceAccountUser`
   - `roles/storage.admin`
4. Create JSON key and add to GitHub secrets

### Manual Deployment
```bash
# Build and push
docker build -t gcr.io/PROJECT_ID/repograph-ai:latest .
docker push gcr.io/PROJECT_ID/repograph-ai:latest

# Deploy
gcloud run deploy repograph-ai \
  --image gcr.io/PROJECT_ID/repograph-ai:latest \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📊 Monitoring Workflows

### View Status
- GitHub → Actions tab
- Filter by workflow name
- Check run history

### Debugging Failed Runs
1. Click on failed workflow run
2. Expand failed job
3. Check step logs
4. Download artifacts if needed

---

## 🔄 Usage Examples

### Trigger Manual Deployment
```bash
# Using GitHub CLI
gh workflow run ci-cd.yml \
  --ref main \
  -f environment=production
```

### Create a Release
```bash
# Tag and push
git tag v1.0.0
git push origin v1.0.0

# Or manually
gh workflow run release.yml \
  -f version=1.0.0 \
  -f release_type=release
```

### Force Dependency Update
```bash
gh workflow run dependency-updates.yml \
  -f update_type=security
```

---

## 📈 Best Practices

1. **Always run tests locally** before pushing
2. **Use conventional commits** for changelog generation
3. **Review security alerts** promptly
4. **Keep dependencies updated** via Dependabot
5. **Use feature branches** and PRs
6. **Tag releases** with semantic versions

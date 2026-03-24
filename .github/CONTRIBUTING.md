# RioVPN GitHub Actions Configuration

## Workflows

### ci.yml - CI/CD Pipeline

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**

1. **Lint** (10 min timeout)
   - Flake8 linting
   - Black code style check
   - Mypy type checking

2. **Test** (20 min timeout)
   - Python 3.11 & 3.12
   - Pytest with coverage
   - Codecov upload
   - Requires: lint

3. **Security** (15 min timeout)
   - Bandit security scan
   - Safety dependency check
   - Pip-audit
   - Requires: lint

4. **Docker** (20 min timeout)
   - Build bot image
   - Build worker image
   - Test images
   - Requires: test

5. **Deploy** (30 min timeout)
   - Production deployment
   - Only on main branch push
   - Requires: test, security, docker

6. **Notify**
   - Summary of all jobs
   - Always runs

### scheduled.yml - Scheduled Tasks

**Triggers:**
- Every Monday at 00:00 UTC
- Manual dispatch

**Jobs:**

1. **Check Dependencies**
   - pip-review for updates
   - Creates GitHub issue

2. **Code Quality Report**
   - Radon complexity analysis
   - Maintainability index
   - Test coverage

3. **Database Backup**
   - Conditional on DATABASE_URL secret
   - 30-day retention

## Required Secrets

| Secret | Description | Required For |
|--------|-------------|--------------|
| `CODECOV_TOKEN` | Codecov upload token | Coverage reports |
| `DEPLOY_TOKEN` | Deployment API token | Production deploy |
| `DATABASE_URL` | Database connection string | Backup job |
| `BACKUP_BUCKET` | S3 bucket for backups | Backup job |

## Configuration Files

### .flake8
```ini
[flake8]
max-line-length = 127
max-complexity = 10
exclude = .git,__pycache__,venv,.venv
```

### pyproject.toml
```toml
[tool.black]
line-length = 127
target-version = ['py311']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

## Badges

Add these to your README.md:

```markdown
[![CI/CD](https://github.com/yourusername/riovpn/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/riovpn/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/yourusername/riovpn/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/riovpn)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## Manual Triggers

All workflows can be triggered manually:

1. Go to **Actions** tab
2. Select workflow
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow**

## Troubleshooting

### Workflow not running?

1. Check if Actions are enabled in repository settings
2. Verify workflow files are in `.github/workflows/`
3. Check YAML syntax with yamllint

### Tests failing?

```bash
# Run locally
pytest -v --tb=short

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Docker build failing?

```bash
# Build locally
docker build -t riovpn-bot:test .

# Test
docker run --rm riovpn-bot:test python -m pytest
```

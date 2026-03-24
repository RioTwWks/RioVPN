# CI/CD Guide

## Overview

RioVPN uses GitHub Actions for continuous integration and deployment.

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**

| Job | Description | Duration | Dependencies |
|-----|-------------|----------|--------------|
| `lint` | Code style and type checking | 10 min | None |
| `test` | Unit and integration tests | 20 min | lint |
| `security` | Security scans | 15 min | lint |
| `docker` | Build Docker images | 20 min | test |
| `deploy` | Production deployment | 30 min | test, security, docker |
| `notify` | Status notification | - | all |

### 2. Scheduled Tasks (`.github/workflows/scheduled.yml`)

**Triggers:**
- Every Monday at 00:00 UTC
- Manual dispatch

**Jobs:**

| Job | Description | Duration |
|-----|-------------|----------|
| `check-dependencies` | Check for package updates | 15 min |
| `code-quality` | Code quality report | 20 min |
| `backup` | Database backup | 10 min |

## Setup

### 1. Enable GitHub Actions

1. Go to repository **Settings** → **Actions** → **General**
2. Select **Allow all actions and reusable workflows**
3. Click **Save**

### 2. Configure Secrets

Go to **Settings** → **Secrets and variables** → **Actions**

**Required secrets:**

| Secret | Description | Example |
|--------|-------------|---------|
| `CODECOV_TOKEN` | Codecov upload token | `abc123...` |
| `DEPLOY_TOKEN` | Deployment API token | `deploy_abc123...` |
| `DATABASE_URL` | Production database URL | `postgresql+asyncpg://...` |
| `BACKUP_BUCKET` | S3 bucket for backups | `riovpn-backups` |

**How to get Codecov token:**

1. Go to [codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Add your repository
4. Copy the token from Settings

### 3. Configure Environments

Go to **Settings** → **Environments** → **New environment**

**Production environment:**

1. Name: `production`
2. Deployment branches: `main` only
3. Required reviewers: (add reviewers)
4. Environment secrets: (add if different from repo secrets)

## Usage

### Manual Trigger

1. Go to **Actions** tab
2. Select workflow
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow**

### Skip Jobs

Add to commit message:

```
[skip ci] - Skip all CI checks
[ci skip] - Skip all CI checks
[skip tests] - Skip test job only
```

### Test Locally

```bash
# Run same checks as CI
pip install flake8 black mypy pytest

# Lint
flake8 src/ tests/
black --check src/ tests/
mypy src/ --ignore-missing-imports

# Tests
pytest --cov=src --cov-fail-under=70

# Security
pip install bandit safety
bandit -r src/
safety check

# Docker
docker build -t riovpn-bot:test .
docker run --rm riovpn-bot:test python -m pytest
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.flake8` | Flake8 linting rules |
| `pyproject.toml` | Black, mypy, pytest, coverage config |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `.github/workflows/scheduled.yml` | Scheduled tasks |
| `.coveragerc` | Coverage configuration |
| `pytest.ini` | Pytest configuration |

## Badges

Add to `README.md`:

```markdown
[![CI/CD](https://github.com/yourusername/riovpn/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/riovpn/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/yourusername/riovpn/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/yourusername/riovpn)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
```

## Troubleshooting

### Workflow not running?

1. **Check Actions enabled:**
   - Settings → Actions → General
   - Ensure "Allow all actions" is selected

2. **Check workflow syntax:**
   ```bash
   # Install yamllint
   pip install yamllint
   
   # Validate workflow files
   yamllint .github/workflows/ci.yml
   ```

3. **Check file location:**
   - Workflows must be in `.github/workflows/`
   - File extension must be `.yml` or `.yaml`

### Tests failing in CI but passing locally?

1. **Check Python version:**
   ```bash
   python --version  # CI uses 3.11 or 3.12
   ```

2. **Check environment variables:**
   ```bash
   # CI sets these automatically
   echo $CI  # should be "true"
   ```

3. **Check database:**
   - CI uses in-memory SQLite
   - Ensure tests don't depend on PostgreSQL-specific features

### Coverage not uploading?

1. **Check token:**
   - Verify `CODECOV_TOKEN` secret is set
   - Token should have `upload` permission

2. **Check coverage file:**
   ```bash
   # Should generate coverage.xml
   pytest --cov=src --cov-report=xml
   ls coverage.xml
   ```

3. **Check workflow:**
   - Verify `actions/upload-artifact` step
   - Check Codecov action version

### Docker build failing?

1. **Test locally:**
   ```bash
   docker build -t riovpn-bot:test .
   docker run --rm riovpn-bot:test python -c "print('OK')"
   ```

2. **Check Dockerfile:**
   - Ensure all paths are correct
   - Verify base image exists

3. **Check disk space:**
   ```bash
   # GitHub runners have ~14GB free
   df -h
   ```

## Deployment Configuration

### Configure Production Deployment

Edit `.github/workflows/ci.yml`:

```yaml
deploy:
  steps:
    # AWS Example
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster riovpn --service bot --force-new-deployment

    # OR Heroku Example
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: "riovpn"
        heroku_email: "your-email@example.com"

    # OR DigitalOcean Example
    - name: Deploy to DigitalOcean
      uses: digitalocean/action-doctl@v2
      with:
        token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

## Best Practices

1. **Keep workflows fast**
   - Use caching (`actions/cache`)
   - Parallelize independent jobs
   - Set appropriate timeouts

2. **Secure secrets**
   - Never echo secrets
   - Use environment-specific secrets
   - Rotate tokens regularly

3. **Test thoroughly**
   - Run same tests locally and in CI
   - Use coverage thresholds
   - Test on multiple Python versions

4. **Monitor costs**
   - GitHub Actions: 2000 minutes/month (free tier)
   - Cancel redundant workflows
   - Use self-hosted runners for heavy jobs

## Monitoring

### Workflow Status

- **Green check** ✅ - All jobs passed
- **Red X** ❌ - Job failed
- **Yellow dot** ⏳ - Job running
- **Blue info** ℹ️ - Job skipped

### Notifications

Configure notifications:

1. Go to **Settings** → **Notifications**
2. Select email/push notifications
3. Choose events to monitor

### Logs

View job logs:

1. Go to **Actions** tab
2. Click on workflow run
3. Click on job name
4. Expand step logs

Download artifacts:

1. Go to workflow run
2. Scroll to **Artifacts** section
3. Click to download

## Cost Optimization

GitHub Actions pricing (free tier):

- 2,000 minutes/month
- 500 MB of packages storage
- Unlimited public repositories

**Tips to reduce usage:**

1. Cancel redundant workflows:
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

2. Use caching:
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

3. Skip unnecessary jobs:
   ```yaml
   if: github.event_name == 'push' && github.ref == 'refs/heads/main'
   ```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Available Actions](https://github.com/marketplace?type=actions)
- [Python Actions Guide](https://docs.github.com/en/actions/guides/building-and-testing-python)

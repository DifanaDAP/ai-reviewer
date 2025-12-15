# AI PR Reviewer v2 🤖

An intelligent, automated code review system powered by AI. Like CodeRabbit, but self-hosted and fully customizable!

**v2 New:** MongoDB storage + Redis queue for review history and future vectorization.

## Quick Start (For Target Repositories)

**Only 1 file needed!** Add this to your repository at `.github/workflows/ai-pr-reviewer.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: YOUR_USERNAME/ai-reviewer@main
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

> **Note:** Replace `YOUR_USERNAME/ai-reviewer` with your actual GitHub username/repo where this action is hosted.

Then add `OPENAI_API_KEY` to your repository secrets. Done! 🎉

---

## Features

| Feature | Description |
|---------|-------------|
| **Security Analysis** | SQL injection, XSS, hardcoded secrets, shell injection |
| **Performance** | N+1 queries, blocking calls, inefficient patterns |
| **Code Style** | Naming conventions, anti-patterns, best practices |
| **PR Structure** | Title format, description, linked issues, screenshots |
| **Test Coverage** | Test file changes, coverage ratio, missing tests |
| **Documentation** | README, CHANGELOG, docstring requirements |
| **AI Review** | LLM-powered deep code analysis using GPT |
| **MongoDB Storage** | 🆕 Save reviews as documents for history/analytics |
| **Redis Queue** | 🆕 Async messaging for future vectorization pipeline |

### Priority Levels

- 🔴 **HIGH** - Blocking issues (security, critical bugs)
- 🟡 **MEDIUM** - Should be addressed
- 🟢 **LOW** - Recommendations
- 💭 **NIT** - Style suggestions

---

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `openai_model` | No | `gpt-4o-mini` | OpenAI model to use |
| `max_tokens` | No | `4096` | Max tokens for response |
| `debug` | No | `false` | Enable debug logging |

---

## Storage Configuration (v2)

Enable MongoDB/Redis storage by setting these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_STORAGE` | `false` | Enable MongoDB + Redis storage |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `ai_reviewer` | Database name |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | (empty) | Redis password (optional) |

### Docker Setup

Start MongoDB, Mongo Express, and Redis locally:

```bash
docker-compose up -d
```

Access Mongo Express UI: http://localhost:8081 (login: `admin` / `admin123`)

---

## Custom Configuration (Optional)

Add `.ai-reviewer.yml` to your repository root:

```yaml
# PR rules
pr_structure:
  title_pattern: "^(feat|fix|docs|style|refactor|test|chore)..."
  require_description: true

# Size limits
pr_size:
  max_files: 20
  max_lines_added: 500

# Ignore patterns
ignore:
  - "*.lock"
  - "dist/*"
```

---

## Architecture

```
ai-reviewer/           ← This repository (GitHub Action)
├── action.yml         # Action definition
├── docker-compose.yml # MongoDB + Redis + Mongo Express
├── ai_reviewer/       # Python source code
│   ├── main.py        # Entry point
│   ├── analyzers/     # 6 code analyzers
│   ├── llm/           # OpenAI integration
│   ├── github/        # GitHub API client
│   └── storage/       # 🆕 MongoDB + Redis clients
└── .ai-reviewer.yml   # Default config

your-repo/             ← Target repository (only 1 file needed!)
└── .github/workflows/
    └── ai-pr-reviewer.yml
```

---

## Local Development

```bash
# Start storage services
docker-compose up -d

# Set environment variables
export GITHUB_TOKEN=ghp_xxxxx
export OPENAI_API_KEY=sk-xxxxx
export PR_NUMBER=1
export REPO=owner/repo
export ENABLE_STORAGE=true  # Enable v2 storage

# Run
python ai_reviewer/main.py
```

---

## Self-Hosting

1. **Fork/Clone** this repository
2. **Push** to your GitHub account
3. **Use** in your projects with `uses: your-username/ai-reviewer@main`

---

## License

MIT License

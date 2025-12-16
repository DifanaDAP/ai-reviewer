# AI PR Reviewer v2 🤖

An intelligent, automated code review system powered by AI. Like CodeRabbit, but self-hosted and fully customizable!

**v2 New:** MongoDB storage for review history.

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

Enable MongoDB storage by setting these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_STORAGE` | `false` | Enable MongoDB storage |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `ai_reviewer` | Database name |

### MongoDB Setup Guide

If you don't have MongoDB installed, here are a few ways to get started:

1.  **MongoDB Atlas (Cloud - Recommended)**
    *   Sign up for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
    *   Create a free cluster.
    *   Get your connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`).

2.  **Local Installation**
    *   **Windows**: Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community).
    *   **Mac**: `brew tap mongodb/brew && brew install mongodb-community`
    *   **Linux**: Follow instructions for your distro on the MongoDB website.

3.  **Docker (If you prefer containers)**
    ```bash
    docker run -d -p 27017:27017 --name mongodb mongo:7
    ```

Once running, update your configuration:
```yaml
mongodb_uri: "mongodb://localhost:27017" # or your Atlas URI
```


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

## Configuration

1. **Environment Config**
   Create a `.ai-reviewer.yml` file in your project root or `~/.ai-reviewer.yml`:

   ```yaml
   github_token: "your-github-token"
   openai_api_key: "your-openai-key"
   
   # Storage Settings
   enable_storage: true
   mongodb_uri: "mongodb://localhost:27017"
   mongodb_database: "ai_reviewer"
   ```

2. **MongoDB Connection**
   This tool is designed to connect to your existing MongoDB instance.
   
   - Ensure your MongoDB server is running.
   - Update `mongodb_uri` in your configuration to point to your MongoDB server (e.g., `mongodb://user:pass@host:port`).

## Usage

### As a GitHub Action

```yaml
name: AI Reviewer
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run AI Reviewer
        uses: your-username/ai-reviewer@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ENABLE_STORAGE: "true"
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
```

### Local Development

1.  **Install Dependencies**
    ```bash
    pip install -r requirements-review.txt
    ```

2.  **Run the Reviewer**
    ```bash
    # Set environment variables
    export GITHUB_TOKEN="your_token"
    export OPENAI_API_KEY="your_key"
    export PR_NUMBER=123
    export REPO="owner/repo"
    export ENABLE_STORAGE="true"
    export MONGODB_URI="mongodb://localhost:27017"

    # Run
    python -m ai_reviewer.main
    ```

---

## Architecture

```
ai-reviewer/           ← This repository (GitHub Action)
├── action.yml         # Action definition
├── ai_reviewer/       # Python source code
│   ├── main.py        # Entry point
│   ├── analyzers/     # 6 code analyzers
│   ├── llm/           # OpenAI integration
│   ├── github/        # GitHub API client
│   └── storage/       # 🆕 MongoDB client
└── .ai-reviewer.yml   # Default config

your-repo/             ← Target repository (only 1 file needed!)
└── .github/workflows/
    └── ai-pr-reviewer.yml
```

---

## Local Development

```bash
# Ensure MongoDB is running first!

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

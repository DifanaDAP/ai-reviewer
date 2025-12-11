# AI PR Reviewer 🤖

An intelligent, automated code review system powered by AI. Like CodeRabbit, but self-hosted and fully customizable!

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

## Example Output

```markdown
## 🤖 AI Code Review

### 📊 Summary
| Metric | Value |
|--------|-------|
| Files Changed | 5 |
| Lines Added | +120 |
| Status | 🟡 Needs Attention |

### 🔴 HIGH Priority (Blocking)
| File | Line | Issue |
|------|------|-------|
| `auth.py` | 45 | SQL injection vulnerability |

### ✅ What's Good
- Good test coverage
- Clear commit messages
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
│   └── github/        # GitHub API client
└── .ai-reviewer.yml   # Default config

your-repo/             ← Target repository (only 1 file needed!)
└── .github/workflows/
    └── ai-pr-reviewer.yml
```

---

## Self-Hosting

1. **Fork/Clone** this repository
2. **Push** to your GitHub account
3. **Use** in your projects with `uses: your-username/ai-reviewer@main`

---

## Local Development

```bash
# Set environment variables
export GITHUB_TOKEN=ghp_xxxxx
export OPENAI_API_KEY=sk-xxxxx
export PR_NUMBER=1
export REPO=owner/repo

# Run
python ai_reviewer/main.py
```

---

## License

MIT License

# Usage Example for Target Repositories

This file shows what users need to add to their repositories that want to use this AI PR Reviewer.

## Quick Setup

Create this file in your repository at `.github/workflows/ai-pr-reviewer.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
  pull_request_review_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: ${{ github.repository }}-${{ github.event.number }}-${{ github.workflow }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: user/ai-reviewer@main  # Replace with your GitHub username/repo
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        with:
          openai_model: 'gpt-4o-mini'
          debug: 'false'
```

## That's it!

Users only need to:
1. Copy the workflow file above
2. Replace `user/ai-reviewer@main` with your actual repo path
3. Add `OPENAI_API_KEY` to their repository secrets
4. Create a PR and the review runs automatically!

#!/bin/bash

# Script to check git status and commit workflow changes

cd "/home/nadeeshame/PycharmProjects/RepoGraph AI"

echo "=== Current Git Status ==="
git status

echo ""
echo "=== Uncommitted Changes ==="
git diff --name-only

echo ""
echo "=== Last 3 Commits ==="
git log --oneline -3

echo ""
echo "=== Checking if workflow files have uncommitted changes ==="
if git diff --quiet .github/workflows/; then
    echo "✅ No uncommitted changes in workflows"
else
    echo "⚠️  Workflows have uncommitted changes"
    echo ""
    echo "To commit these changes, run:"
    echo "git add .github/workflows/"
    echo 'git commit -m "fix: handle missing GCP credentials in CI/CD workflows"'
fi

echo ""
echo "=== Checking for unpushed commits ==="
UNPUSHED=$(git log @{u}..HEAD --oneline 2>/dev/null)
if [ -z "$UNPUSHED" ]; then
    echo "✅ No unpushed commits (or no upstream branch set)"
else
    echo "⚠️ You have unpushed commits:"
    echo "$UNPUSHED"
    echo ""
    echo "To push, run:"
    echo "git push origin master"
fi

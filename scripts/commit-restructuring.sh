#!/bin/bash
# Commit and push project restructuring changes

set -e  # Exit on error

cd "/home/nadeeshame/PycharmProjects/RepoGraph AI"

echo "🔍 Checking current status..."
git status

echo ""
echo "📦 Staging all changes..."
git add -A

echo ""
echo "📝 Creating commit..."
git commit -m "refactor: restructure project and add comprehensive documentation

✨ New Structure:
- Created scripts/ directory and moved test_setup.py
- Added README.md to scripts/, data/, and credentials/ folders
- Added linting configuration (.flake8, pyproject.toml)

📚 Documentation:
- Updated main README.md with new structure
- Added security guidelines in credentials/README.md
- Added data organization guide in data/README.md
- Added scripts usage guide in scripts/README.md

🧹 Cleanup:
- Removed temporary scripts from docs/assets/
- Removed empty docs/assets/ directory

🎯 Benefits:
- Cleaner root directory
- Better organization for new contributors
- Clear security practices documented
- Fixed linting configuration issues

This makes the project more maintainable and easier to understand."

echo ""
echo "🚀 Pushing to GitHub..."
git push origin master

echo ""
echo "✅ Successfully pushed all changes!"
echo ""
echo "📊 Next steps:"
echo "  1. Check GitHub Actions to verify CI/CD passes"
echo "  2. Review the new structure in the GitHub repository"
echo "  3. Verify all README files display correctly"
echo ""
echo "🎉 Project restructuring complete!"

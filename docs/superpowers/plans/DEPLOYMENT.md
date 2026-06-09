# GitHub Pages Deployment Setup

This guide provides comprehensive instructions for deploying the auto-generated schema documentation to GitHub Pages.

## Overview

The schema documentation is automatically generated from JSON and YAML schema files in the `schemas/` directory. The generated documentation includes:

- Interactive schema browser with search and filtering
- Cross-reference visualization between schemas
- Dependency graphs showing schema relationships
- Full schema definitions with descriptions and constraints
- Category organization for easy navigation

## Deployment Architecture

```
┌─ GitHub Repository (qontract-schemas)
│
├─ Source: schemas/ (JSON/YAML schema definitions)
│
├─ Generator: scripts/generate_schema_docs.py
│
├─ Output: docs/ (static HTML/CSS/JSON)
│
└─ GitHub Pages: https://app-sre.github.io/qontract-schemas/
```

## Prerequisites

- GitHub repository with admin or maintainer access
- GitHub Pages enabled for the repository
- Knowledge of GitHub Actions (for CI/CD automation)
- Familiarity with repository settings

## Step 1: Verify Documentation Generation Locally

Before deploying, ensure the documentation generates correctly on your machine:

```bash
cd /path/to/qontract-schemas

# Install dependencies
uv sync

# Generate documentation
make generate-docs

# Verify output
ls -la docs/
# Output should include:
# - index.html (main documentation page)
# - styles.css (styling)
# - schemas.json (data file with all schema information)

# Validate JSON structure
python3 << 'EOF'
import json
with open('docs/schemas.json', 'r') as f:
    data = json.load(f)
    assert 'categories' in data, "Missing categories"
    assert 'schemas' in data, "Missing schemas"
    assert len(data['schemas']) > 0, "No schemas found"
    print(f"✓ Valid: {len(data['schemas'])} schemas in {len(data['categories'])} categories")
EOF
```

Expected output:
```
Generating schema documentation...
Found 163 schema files
Successfully parsed 163 schemas
Generated docs/schemas.json
✓ Valid: 163 schemas in 13 categories
```

## Step 2: Enable GitHub Pages in Repository Settings

1. Navigate to GitHub repository: `https://github.com/app-sre/qontract-schemas`
2. Click **Settings** (top navigation)
3. Click **Pages** (left sidebar under "Code and automation")
4. Under "Build and deployment":
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select `main`
   - **Folder**: Select `/ (root)` or `/docs` (see note below)
5. Click **Save**

### Important: Branch and Folder Selection

- **Production Deployment**: Use `/docs` folder from `main` branch
  - This assumes documentation is committed to `docs/` directory
  - Cleanest approach for production

- **Alternative**: Use `gh-pages` branch
  - Requires separate GitHub Actions workflow to auto-generate and push to `gh-pages`
  - Recommended for automated documentation updates on every merge

## Step 3: Configure GitHub Pages Deployment Branch (Recommended)

For automated deployment on every push, use GitHub Actions to generate and deploy to `gh-pages` branch:

### 3A: Create GitHub Actions Workflow

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Schema Documentation to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'schemas/**'
      - 'scripts/generate_schema_docs.py'
      - '.github/workflows/deploy-docs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install UV
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: uv sync

      - name: Generate documentation
        run: make generate-docs

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: './docs'

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

### 3B: Configure GitHub Pages for gh-pages Branch

1. Go to **Settings** > **Pages**
2. Under "Build and deployment":
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select `gh-pages`
   - **Folder**: Select `/ (root)`
3. Click **Save**

GitHub Actions will automatically build and deploy to `gh-pages` on every push to `main` that affects schema files or the generator script.

## Step 4: Verify Deployment

After deploying, verify the documentation is accessible:

1. Wait 1-2 minutes for GitHub Pages to build and deploy
2. Visit: `https://app-sre.github.io/qontract-schemas/`
3. Verify:
   - Page loads without errors
   - Schema list displays all categories
   - Search functionality works
   - Cross-references render correctly

### Troubleshooting Deployment

**Issue**: GitHub Pages URL shows 404 error

Solution:
- Verify repository is public (private repos require GitHub Enterprise)
- Check that `docs/` folder contains `index.html`
- Wait 2-3 minutes for GitHub Pages to refresh
- Check GitHub Pages status under Settings > Pages

**Issue**: Documentation looks broken or styles missing

Solution:
- Verify `styles.css` is in `docs/` folder
- Check browser developer console for CORS errors
- Ensure file paths in `index.html` are correct relative to `/qontract-schemas/` prefix

**Issue**: GitHub Actions workflow fails

Solution:
- Check workflow run logs: **Actions** tab > select workflow > failed run
- Verify `make generate-docs` works locally
- Check Python version compatibility (requires 3.12+)
- Verify UV installation works in CI environment

## Step 5: Update Documentation Automatically

The GitHub Actions workflow automatically regenerates and deploys documentation when:

1. **Schema files** (`schemas/**/*.yml` or `schemas/**/*.json`) are modified
2. **Generator script** (`scripts/generate_schema_docs.py`) is updated
3. **Workflow itself** (`.github/workflows/deploy-docs.yml`) is changed
4. **Manual trigger** via Actions tab > "Deploy Schema Documentation" > "Run workflow"

### Manual Trigger Example

```bash
# To manually trigger from command line:
gh workflow run deploy-docs.yml --repo app-sre/qontract-schemas
```

## Step 6: Commit and Push Changes

Commit the generated documentation and workflow:

```bash
cd /path/to/qontract-schemas

# Add generated files and workflow
git add docs/schemas.json docs/index.html docs/styles.css .github/workflows/deploy-docs.yml

# Create descriptive commit
git commit -m "Add schema documentation generation and GitHub Pages deployment

- Generated interactive schema browser from 163 schema files
- Includes cross-references and dependency visualization
- Set up automated GitHub Pages deployment via Actions
- Docs available at: https://app-sre.github.io/qontract-schemas/"

# Push to main branch
git push origin main
```

## Step 7: Monitor Documentation Updates

### Check Deployment Status

1. Go to **Actions** tab on GitHub
2. Select **Deploy Schema Documentation to GitHub Pages** workflow
3. Monitor recent runs:
   - Green checkmark: Deployment successful
   - Red X: Deployment failed (check logs)
   - Blue hourglass: Deployment in progress

### View Deployment History

```bash
# List recent deployments
gh api repos/app-sre/qontract-schemas/deployments \
  --jq '.[] | {id, environment, state, created_at}'
```

## Maintenance and Updates

### When to Regenerate Documentation

- After adding new schema files to `schemas/`
- After updating schema descriptions or properties
- After moving or renaming schema files
- Automatically via GitHub Actions on every push

### Manual Regeneration

If you need to manually regenerate without pushing to GitHub:

```bash
# Ensure you're in the repository root
cd /path/to/qontract-schemas

# Regenerate documentation
make generate-docs

# Verify output
ls -la docs/
python3 scripts/generate_schema_docs.py --schemas-dir schemas --output-dir docs

# Test locally before pushing
cd docs && python -m http.server 8000
# Visit http://localhost:8000 in browser
```

### Cleaning Up Generated Files

```bash
# Remove all generated documentation
make clean

# Removes:
# - docs/schemas.json
# - docs/index.html
# - docs/styles.css
# - build artifacts
```

## Customization

### Modifying Documentation Appearance

Edit `scripts/generate_schema_docs.py` to customize:

- Schema categorization logic
- Dependency visualization
- HTML template structure
- CSS styling in `docs/styles.css`

Example: Change documentation title

```bash
# Find and modify the title in generate_schema_docs.py
grep -n "schema documentation" scripts/generate_schema_docs.py
# Update the title string and regenerate
make generate-docs
git add docs/
git commit -m "Update schema documentation title"
git push origin main
```

### Custom Domain

To use a custom domain (e.g., `schemas.app-sre.io`):

1. GitHub Pages Settings > Custom domain
2. Enter domain: `schemas.app-sre.io`
3. Add DNS CNAME record pointing to: `app-sre.github.io`
4. GitHub verifies DNS configuration automatically

## Continuous Integration Checklist

- [ ] `make test` passes locally
- [ ] `make generate-docs` produces valid output
- [ ] `docs/schemas.json` contains all 163+ schemas
- [ ] Documentation loads without console errors
- [ ] Search and filtering work correctly
- [ ] Cross-references render properly
- [ ] All links are relative to `/qontract-schemas/` prefix
- [ ] GitHub Actions workflow runs successfully
- [ ] GitHub Pages status shows "Ready" in Settings
- [ ] Live URL is accessible and displays correctly

## Rollback Procedure

If deployed documentation has issues:

```bash
# Option 1: Revert to previous commit
git revert <commit-hash>
git push origin main
# GitHub Actions automatically redeploys with previous docs

# Option 2: Disable GitHub Pages temporarily
# Settings > Pages > Source > None
# Then re-enable after fixing issues

# Option 3: Emergency manual deployment
make generate-docs
git add docs/
git commit -m "Emergency hotfix: regenerate documentation"
git push origin main
```

## Support and Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 404 on GitHub Pages | Repository is private | Switch to public or use Enterprise |
| Missing styles | CSS file not deployed | Verify `docs/styles.css` exists and committed |
| Stale docs | GitHub Pages cache | Wait 5 minutes or clear cache (Ctrl+Shift+R) |
| Broken links | Wrong path prefix | Update paths to `/qontract-schemas/` |
| Generator fails | Python version mismatch | Ensure Python 3.12+, run `uv sync` |
| Actions job fails | Missing dependencies | Check that `make generate-docs` works locally |

### Testing Locally Before Deployment

```bash
# Complete local validation
cd /path/to/qontract-schemas

# Run tests
uv run pytest test/test_schema_docs_generator.py -v

# Generate docs
make generate-docs

# Start local server
cd docs && python -m http.server 8000

# Visit http://localhost:8000
# Test all features before pushing
```

## Related Documentation

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Schema Generator Script](../scripts/generate_schema_docs.py)
- [Schema Documentation Structure](../AGENTS.md)

## Success Criteria

Deployment is successful when:

1. ✓ Documentation generates without errors: `make generate-docs`
2. ✓ All tests pass: `make test`
3. ✓ `docs/` folder contains `index.html`, `styles.css`, `schemas.json`
4. ✓ GitHub Pages is enabled in Settings
5. ✓ GitHub Actions workflow runs successfully
6. ✓ Documentation is accessible at `https://app-sre.github.io/qontract-schemas/`
7. ✓ All 163+ schemas are visible in the browser
8. ✓ Search and filtering functionality works
9. ✓ Cross-references and dependencies display correctly

---

**Last Updated**: 2026-06-09
**Documentation Version**: 1.0

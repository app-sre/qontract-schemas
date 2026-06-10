# Schema Documentation Generator

This directory contains the schema documentation generator and templates.

## Files

- `generate_schema_docs.py` - Main generator script
- `templates/index.html` - HTML viewer template
- `templates/styles.css` - Stylesheet

## Usage

Generate documentation:

```bash
make generate-docs
```

Or run directly:

```bash
uv run python scripts/generate_schema_docs.py --schemas-dir schemas --output-dir docs
```

## Options

- `--schemas-dir` - Directory containing schema files (default: `schemas`)
- `--output-dir` - Output directory for generated files (default: `docs`)

## Output

Generates three files in the output directory:

- `schemas.json` - All parsed schema data
- `index.html` - Single-page viewer application
- `styles.css` - Styling

## Local Development

View the generated docs locally:

```bash
cd docs
python -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Testing

Run tests:

```bash
uv run pytest test/test_schema_docs_generator.py -v
```

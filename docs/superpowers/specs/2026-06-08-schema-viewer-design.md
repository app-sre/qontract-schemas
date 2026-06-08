# Schema Visualization Tool - Design Specification

**Date:** 2026-06-08  
**Status:** Approved  
**Target Audience:** App-SRE team members and service owners/external contributors

## Overview

A web-based visualization tool for qontract-schemas that makes it easier to browse, understand, and navigate JSON schemas. The tool addresses the difficulty of working with large YAML schema files that reference each other, providing a clean interface with collapsible schema lists, property tables with detailed metadata, clickable cross-references, and a dependency tree view.

## Goals

1. **Improve schema discoverability** - Make it easy to find schemas by category and name
2. **Clarify schema structure** - Show properties, types, constraints, and requirements in a scannable format
3. **Visualize dependencies** - Display property-level references between schemas with full JSON paths
4. **Serve multiple audiences** - Balance quick reference for experienced SREs with guidance for newcomers
5. **Minimal maintenance** - Static site generation with no runtime dependencies or hosting complexity

## Non-Goals

- Schema editing or validation (read-only visualization)
- Integration with app-interface data (only shows schema structure)
- Real-time schema updates (regenerates on CI/CD)
- Examples pulled from actual app-interface YAML files (future enhancement)

## Architecture

### Deployment Model

**Static site hosted on GitHub Pages:**
- Python script generates static HTML/CSS/JS files
- Published to `docs/` directory or `gh-pages` branch
- Automatically rebuilt on schema changes via CI/CD
- No server-side components required

### Components

#### 1. Build-Time Generator (`scripts/generate_schema_docs.py`)

Python script that:
- Scans `schemas/` directory recursively
- Parses YAML/JSON schema files using `anymarkup` (existing dependency)
- Extracts property definitions, types, descriptions, constraints, cross-references
- Builds dependency graph with property-level paths
- Computes reverse dependencies (what references this schema)
- Outputs `schemas.json` containing all parsed data
- Copies static assets to `docs/` directory

**Dependencies:**
- Uses existing project dependencies: `PyYAML`, `anymarkup`, `jsonschema`
- No additional packages required

#### 2. Runtime Viewer (Single-Page App)

Vanilla JavaScript application with:
- `docs/index.html` - Single-page app shell
- `docs/schemas.json` - All schema data (generated)
- `docs/styles.css` - Styling

**Technology:**
- Pure HTML/CSS/JavaScript (ES6+)
- No build step or framework dependencies
- Targets modern browsers (Chrome, Firefox, Safari, Edge - last 2 versions)

### File Structure

```
qontract-schemas/
├── scripts/
│   └── generate_schema_docs.py    # Python generator
├── docs/                           # Generated output (committed to repo)
│   ├── index.html                  # Single-page app
│   ├── schemas.json                # All schema data
│   └── styles.css                  # Styling
├── Makefile                        # Add 'generate-docs' target
└── .github/workflows/              # CI/CD: auto-generate on merge
    └── deploy-docs.yml
```

## Data Model

### schemas.json Structure

```json
{
  "categories": [
    {
      "name": "app-sre",
      "schemas": ["app-1.yml", "escalation-policy-1.yml", ...]
    },
    {
      "name": "aws",
      "schemas": ["account-1.yml", "group-1.yml", ...]
    }
  ],

  "schemas": {
    "app-sre/app-1.yml": {
      "path": "app-sre/app-1.yml",
      "version": "1.0",
      "description": "Application schema",

      "properties": [
        {
          "name": "name",
          "type": "string",
          "required": true,
          "description": "Application name",
          "constraints": {
            "pattern": "^[A-Za-z0-9][A-Za-z0-9-_\\.]{0,30}[A-Za-z0-9]$",
            "ref": "/common-1.json#/definitions/extendedIdentifier"
          }
        },
        {
          "name": "product",
          "type": "object (ref)",
          "required": false,
          "description": null,
          "schemaRef": "app-sre/product-1.yml",
          "propertyPath": ".product"
        },
        {
          "name": "onboardingStatus",
          "type": "enum",
          "required": true,
          "description": null,
          "constraints": {
            "enum": ["Proposed", "InProgress", "TransitionPeriod", "OnBoarded", "OffBoarding", "BestEffort"]
          }
        }
      ],

      "dependencies": [
        {
          "propertyPath": ".product",
          "targetSchema": "app-sre/product-1.yml"
        },
        {
          "propertyPath": ".escalationPolicy",
          "targetSchema": "app-sre/escalation-policy-1.yml"
        },
        {
          "propertyPath": ".codeComponents[].gitlabHousekeeping.labels_allowed[].role",
          "targetSchema": "access/role-1.yml",
          "isArray": true,
          "isNested": true
        }
      ],

      "referencedBy": [
        {
          "schema": "app-sre/app-1.yml",
          "propertyPath": ".parentApp"
        },
        {
          "schema": "openshift/namespace-1.yml",
          "propertyPath": ".app"
        }
      ]
    }
  }
}
```

### Key Design Decisions

1. **Categories array** - Enables sidebar grouping by directory (app-sre/, aws/, etc.)
2. **Schemas keyed by path** - Fast O(1) lookup when clicking references
3. **Flat properties list** - Easier to render as a table than nested object structure
4. **Property-level dependencies** - Shows full JSON path (e.g., `.codeComponents[].gitlabHousekeeping.labels_allowed[].role`) so users understand where references live
5. **Constraints object** - Captures all validation rules: patterns, enums, formats, min/max values, defaults
6. **Reverse dependencies** - Shows which schemas reference this one (computed during generation)

## User Interface

### Layout

**Three-panel layout:**

1. **Header** (fixed, 60px height)
   - Title: "Qontract Schema Viewer"
   - Global search bar (300px width)

2. **Sidebar** (fixed, 280px width)
   - Collapsible category tree
   - Schema count badges per category
   - Selected schema highlighted
   - Scrollable list

3. **Main Panel** (flexible width)
   - Schema header with path and version
   - Two tabs: "Properties" and "Dependencies"
   - Content area (scrollable)

### Properties Tab

**Table columns:**
- **Property** - Name in monospace font, bold
- **Type** - Color-coded badge (string=gray, enum=yellow, ref=blue)
- **Description** - Full description text, or "(no description)" in gray
- **Required** - Checkmark (✓) or dash (-)

**Table features:**
- Expandable rows: Click to show full constraints (patterns, min/max, defaults, format)
- Reference highlighting: `$ref` properties have light yellow background
- Clickable links: Reference type properties link to target schema
- Sorting: Click column headers to sort (initially sorted by required → name)

**Property details (expanded row):**
```
Constraints:
  • Pattern: ^[A-Za-z0-9][A-Za-z0-9-_\.]{0,30}[A-Za-z0-9]$
  • Format: email
  • Default: "active"
  • Min length: 1
  • Max length: 100
```

### Dependencies Tab

**Content:**

1. **Stats summary** (top)
   - Total schemas referenced: 12
   - Total reference properties: 18

2. **Dependency tree** (main content)
   ```
   📄 app-sre/app-1.yml
     ├─ .product
        → app-sre/product-1.yml
     ├─ .parentApp
        → app-sre/app-1.yml [SELF-REF]
     ├─ .escalationPolicy
        → app-sre/escalation-policy-1.yml
     ├─ .dependencies[]
        → dependencies/dependency-1.yml [ARRAY]
     ├─ .codeComponents[].gitlabHousekeeping.labels_allowed[].role
        → access/role-1.yml [NESTED]
     └─ .glitchtipProjects[]
        → dependencies/glitchtip-project-1.yml [ARRAY]
   ```

3. **Reverse dependencies** (bottom, optional)
   ```
   Referenced By:
     • app-sre/app-1.yml → .parentApp
     • openshift/namespace-1.yml → .app
   ```

**Visual elements:**
- Property paths: Blue background highlight
- Tree characters: `├─` and `└─` for hierarchy
- Badges:
  - `[SELF-REF]` (yellow) - Schema references itself
  - `[ARRAY]` (gray) - Array of references
  - `[NESTED]` (gray) - Deeply nested reference (3+ levels)
  - `[MISSING]` (red) - Broken reference (target doesn't exist)
- Clickable schema links for navigation

### Search Functionality

**Global search bar:**
- Searches schema names, property names, property descriptions, schema paths
- Real-time filtering (debounced 200ms)
- Case-insensitive substring matching
- Filters sidebar (shows only matching schemas) and main panel (highlights matching properties)

**Search behavior:**
- Empty search: Show all schemas
- Results ranked: exact match > starts with > contains
- Matching properties highlighted with yellow background
- "No results" message when nothing matches
- Clear button (X) to reset search

**Example queries:**
- "app-1" → Shows app-sre/app-1.yml
- "escalation" → Shows escalation-policy-1.yml and properties named escalationPolicy
- "aws/" → Shows all AWS schemas

### Interaction Patterns

**Navigation:**
1. Click category in sidebar → Expand/collapse schema list
2. Click schema in sidebar → Load schema in main panel
3. Click `$ref` link in properties table → Navigate to referenced schema
4. Click `$ref` link in dependencies tree → Navigate to referenced schema
5. Browser back/forward buttons work (URL hash updates)

**Property details:**
1. Click property row → Expand to show constraints
2. Click again → Collapse details

**Mobile responsive:**
- Sidebar collapses to hamburger menu on screens <768px
- Properties table switches to card layout on small screens
- Search bar full width on mobile

### Visual Design

**Color palette:**
- Primary: #007bff (blue) - Links, active elements
- Success: #28a745 (green) - Stats, positive indicators
- Warning: #ffc107 (yellow) - Self-refs, highlights
- Danger: #dc3545 (red) - Missing refs, errors
- Gray scale: #f8f9fa (light bg), #dee2e6 (borders), #6c757d (muted text), #2c3e50 (dark text)

**Typography:**
- Headers: System font stack (sans-serif)
- Body: System font stack
- Code/paths: Monospace (Consolas, Monaco, 'Courier New')

**Type badges:**
- String: Gray (#e9ecef)
- Enum: Yellow (#fff3cd)
- Ref: Blue (#d4edff)
- Number: Cyan (#d1ecf1)
- Boolean: Purple (#e7d4f8)

## Python Generator Implementation

### Script: `scripts/generate_schema_docs.py`

**Core algorithm:**

```python
def generate_schema_docs():
    # 1. Scan schemas directory
    schema_files = scan_schemas_directory("schemas/")
    
    # 2. Parse each schema
    schemas = {}
    for file_path in schema_files:
        schema_data = parse_schema_file(file_path)
        schemas[file_path] = schema_data
    
    # 3. Build dependency graph
    for schema_path, schema_data in schemas.items():
        dependencies = extract_dependencies(schema_data)
        schema_data["dependencies"] = dependencies
    
    # 4. Compute reverse dependencies
    reverse_deps = build_reverse_dependencies(schemas)
    for schema_path, refs in reverse_deps.items():
        schemas[schema_path]["referencedBy"] = refs
    
    # 5. Build categories
    categories = build_categories(schemas)
    
    # 6. Output JSON
    output = {
        "categories": categories,
        "schemas": schemas
    }
    write_json("docs/schemas.json", output)
    
    # 7. Copy static assets
    copy_file("scripts/templates/index.html", "docs/index.html")
    copy_file("scripts/templates/styles.css", "docs/styles.css")
```

### Key Functions

**`parse_schema_file(file_path)`**
- Load YAML/JSON using `anymarkup.parse_file()`
- Extract: `$schema`, `version`, `description`, `properties`, `required`
- For each property:
  - Extract type, description
  - Detect constraints: `pattern`, `enum`, `format`, `minimum`, `maximum`, `default`, `minLength`, `maxLength`
  - Resolve `$ref` to common-1.json definitions
  - Extract `$schemaRef` for cross-references
- Return normalized schema dict

**`extract_dependencies(schema_data, property_path="")`**
- Recursively walk schema properties
- Track current JSON path (e.g., `.codeComponents[].role`)
- When `$schemaRef` found:
  - Record: `{propertyPath, targetSchema, isArray, isNested}`
  - `isArray`: property type is "array"
  - `isNested`: property path has 3+ levels
- Return list of dependencies

**`build_reverse_dependencies(schemas)`**
- For each schema's dependencies:
  - Add reverse link: `targetSchema.referencedBy.append({schema, propertyPath})`
- Return dict of schema → list of references

**`build_categories(schemas)`**
- Group schemas by directory (first path segment)
- Sort schemas within each category
- Return list of `{name, schemas}` objects

### Error Handling

**File parsing errors:**
- Try to parse with anymarkup
- On error: Log warning, skip file, continue processing
- Track skipped files and report at end

**Broken references:**
- If `$schemaRef` points to non-existent schema:
  - Mark with `"broken": true` in dependency object
  - Generator logs warning
  - UI shows `[MISSING]` badge

**Missing descriptions:**
- Store as `null` in JSON
- UI displays "(no description)" in gray text

**Circular references:**
- Detect during dependency graph building
- Allow (don't fail), mark with `"circular": true`
- UI shows `[CIRCULAR]` badge if detected

### Validation

Before writing output:
- Verify all `targetSchema` paths exist in `schemas` object
- Check JSON structure matches expected format
- Validate required fields present

### Integration

**Makefile target:**
```makefile
generate-docs:
	uv run python scripts/generate_schema_docs.py
```

**CI/CD (`.github/workflows/deploy-docs.yml`):**
```yaml
name: Deploy Schema Docs
on:
  push:
    branches: [main]
    paths:
      - 'schemas/**'
      - 'scripts/generate_schema_docs.py'
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Generate docs
        run: make generate-docs
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## Error Handling and Edge Cases

### Schema Parsing Errors

**Malformed YAML/JSON:**
- Log warning with file path and error
- Skip file, continue processing
- Report all skipped files at end of generation

**Missing required fields:**
- If schema missing `$schema`: Log warning, use path as identifier
- If schema missing `properties`: Treat as empty schema
- If schema missing `version`: Default to "unknown"

### Broken References

**Non-existent `$schemaRef`:**
- Mark dependency as `"broken": true`
- UI displays link with `[MISSING]` badge in red
- Clicking shows error message: "Target schema not found: {path}"

### Circular References

**Detection:**
- During dependency traversal, track visited schemas
- If schema references itself (directly or indirectly): Mark as `"circular": true`
- Don't fail generation, allow circular refs

**Display:**
- Show with `[CIRCULAR]` badge
- Link still works (navigates to target)

### Large Schemas

**Many properties (>100):**
- Properties table shows first 50, "Load more" button for rest
- Dependency tree fully rendered (unlikely to exceed 100 deps)

**Large JSON bundle (>5MB):**
- Consider warning during generation
- Future optimization: Split into category bundles if needed

### Runtime Errors

**Failed to load schemas.json:**
- Show error page: "Failed to load schema data. Please regenerate using `make generate-docs`."
- Display error details if available

**JavaScript disabled:**
- Static message in `<noscript>`: "This tool requires JavaScript. Please enable it or view schemas directly on GitHub."

### Browser Compatibility

**Target:**
- Modern browsers: Chrome, Firefox, Safari, Edge (last 2 versions)
- Use ES6+ features (no transpilation)

**Graceful degradation:**
- Collapsible elements: Use `<details>` element where possible
- Search: Basic substring match (no fancy fuzzy logic initially)

## Testing Strategy

### Generator Tests

**Unit tests (`test/test_schema_docs_generator.py`):**
- Test schema parsing: YAML, JSON, malformed files
- Test dependency extraction: simple refs, nested refs, arrays
- Test reverse dependency computation
- Test category building
- Test constraint extraction: patterns, enums, formats

**Integration tests:**
- Run generator on `schemas/` directory
- Validate output JSON structure
- Check all schemas parsed successfully
- Verify no broken references (or expected broken refs documented)

### UI Tests

**Manual testing checklist:**
- [ ] Sidebar: Expand/collapse categories
- [ ] Sidebar: Click schema loads in main panel
- [ ] Properties tab: All columns display correctly
- [ ] Properties tab: Expand row shows constraints
- [ ] Properties tab: Click ref link navigates to target
- [ ] Dependencies tab: Tree renders correctly
- [ ] Dependencies tab: Stats accurate
- [ ] Dependencies tab: Click ref link navigates
- [ ] Search: Filters sidebar and main panel
- [ ] Search: Highlights matching properties
- [ ] Browser back/forward navigation works
- [ ] Mobile: Sidebar collapses to menu
- [ ] Mobile: Properties table switches to cards

**Automated tests (future):**
- Playwright/Cypress for end-to-end UI testing
- Test search, navigation, tab switching

## Deployment

### GitHub Pages Setup

1. **Enable GitHub Pages** in repository settings
2. **Source:** Deploy from `docs/` directory on `main` branch (or `gh-pages` branch)
3. **URL:** `https://app-sre.github.io/qontract-schemas/`

### Manual Deployment

```bash
# Generate docs locally
make generate-docs

# Commit to repository
git add docs/
git commit -m "Update schema documentation"
git push origin main

# GitHub Pages will auto-deploy
```

### Automated Deployment

CI/CD workflow (`.github/workflows/deploy-docs.yml`) runs on:
- Push to `main` branch
- Changes to `schemas/**` or `scripts/generate_schema_docs.py`

## Future Enhancements

### Phase 2 (Post-MVP)

1. **Schema comparison** - Compare two versions of a schema side-by-side
2. **Example values** - Pull real examples from app-interface data files
3. **Validation preview** - Show example YAML that would validate against schema
4. **GraphQL schema integration** - Show relationship to GraphQL schema definitions
5. **Export** - Download schema as OpenAPI spec or other formats
6. **Dark mode** - Toggle between light and dark themes
7. **Bookmarkable URLs** - Deep links to specific schemas (hash routing)
8. **Advanced search** - Fuzzy matching, regex support, filter by type/required
9. **Schema diff view** - Compare current vs previous version (integrate with git history)
10. **Usage statistics** - Show which schemas are most referenced

### Long-term

1. **Interactive playground** - Validate YAML against schema in browser
2. **Schema evolution tracking** - Show version history and breaking changes
3. **Generate code** - Create Python dataclasses or TypeScript types from schemas
4. **Integration with visual-qontract** - Link to actual app-interface data instances

## Success Metrics

**Adoption:**
- Number of unique visitors to schema docs site
- Engagement: average session duration, pages per session

**Effectiveness:**
- Reduction in Slack questions about schema structure
- Faster onboarding for new service owners (measured via survey)
- Time to complete schema-related tasks (baseline vs 3 months post-launch)

**Quality:**
- Zero broken references in generated docs
- <3s page load time on typical connection
- Mobile usability score >90

## Open Questions

None - all design decisions approved.

## Appendix

### File Size Estimates

**schemas.json:**
- ~150 schema files
- Average 20 properties per schema
- Estimated size: 800KB - 1.2MB

**index.html + styles.css:**
- Minimal HTML structure: ~20KB
- CSS: ~15KB
- Total: ~35KB

**Total bundle:** ~850KB - 1.25MB (acceptable for modern web)

### Alternative Approaches Considered

**Approach B: Embedded Data in HTML**
- Single file with data embedded as JS variable
- Rejected: Harder to debug, full regeneration on any change

**Approach C: Lazy-Loading Individual Schema Files**
- Separate JSON file per schema
- Rejected: Overkill for current schema count, adds complexity

### References

- JSON Schema specification: https://json-schema.org/
- GitHub Pages documentation: https://docs.github.com/en/pages
- Existing qontract-schemas README: `/home/essilva/workspace/qontract-schemas/README.md`
- Existing project dependencies: `/home/essilva/workspace/qontract-schemas/pyproject.toml`

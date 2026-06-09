# Schema Viewer UI Improvements Design

**Date:** 2026-06-09

## Goal

Enhance the existing qontract-schemas web viewer with three UI improvements: light/dark mode toggle, single-page layout replacing tabs, and automatic sidebar focus when clicking dependency links.

## Background

The schema viewer (built in 2026-06-08) currently displays schema properties and dependencies in separate tabs. User feedback indicates:
1. Need for dark mode support
2. Preference for seeing properties and dependencies together without tab switching
3. Desire for better navigation when clicking dependency links

## Architecture

**Approach:** Incremental updates to existing template files (`scripts/templates/index.html` and `scripts/templates/styles.css`). No new files, no structural refactoring.

**Modified Files:**
- `scripts/templates/index.html` - Add theme toggle button, remove tab logic, add sidebar focus behavior
- `scripts/templates/styles.css` - Add dark mode CSS variables, update layout for side-by-side view, add highlight animation

**Preserved:**
- Python generator script (`scripts/generate_schema_docs.py`) - no changes needed
- JSON data structure (`docs/schemas.json`) - no changes needed
- Existing search, category collapse, and navigation functionality - unchanged

## Design Sections

### 1. Dark Mode Implementation

#### Theme Detection Strategy

**Initial theme selection (page load):**
1. Check `localStorage.getItem('theme')` for user preference
2. If no stored preference, detect system theme via `window.matchMedia('(prefers-color-scheme: dark)')`
3. Apply theme: `light` or `dark`

**Theme application:**
- Set `data-theme` attribute on `<html>` element: `document.documentElement.setAttribute('data-theme', 'light'|'dark')`
- CSS variables in `:root` and `[data-theme="dark"]` selectors handle color switching

**Persistence:**
- Store user choice in `localStorage.theme` when toggle button clicked
- Theme persists across sessions

#### CSS Variables Structure

**Light mode (default in `:root`):**
```css
:root {
  /* Backgrounds */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #e9ecef;
  
  /* Text */
  --text-primary: #2c3e50;
  --text-secondary: #666666;
  --text-muted: #999999;
  
  /* Borders */
  --border: #dee2e6;
  --border-light: #e9ecef;
  
  /* Header */
  --header-bg: #2c3e50;
  --header-text: #ffffff;
  
  /* Semantic colors (unchanged) */
  --primary: #007bff;
  --success: #28a745;
  --warning: #ffc107;
  --danger: #dc3545;
  
  /* Type badges */
  --type-string-bg: #e9ecef;
  --type-enum-bg: #fff3cd;
  --type-ref-bg: #d4edff;
  --type-array-bg: #e7f3ff;
  --type-object-bg: #f8f9fa;
}
```

**Dark mode overrides in `[data-theme="dark"]`:**
```css
[data-theme="dark"] {
  /* Backgrounds */
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #3a3a3a;
  
  /* Text */
  --text-primary: #e0e0e0;
  --text-secondary: #aaaaaa;
  --text-muted: #888888;
  
  /* Borders */
  --border: #444444;
  --border-light: #555555;
  
  /* Header */
  --header-bg: #0d0d0d;
  --header-text: #e0e0e0;
  
  /* Semantic colors (slightly muted for dark mode) */
  --primary: #64b5f6;
  --success: #66bb6a;
  --warning: #ffca28;
  --danger: #ef5350;
  
  /* Type badges (darker backgrounds, lighter text) */
  --type-string-bg: #3a3a3a;
  --type-enum-bg: #4a4a2d;
  --type-ref-bg: #2d3a4a;
  --type-array-bg: #2d3a4a;
  --type-object-bg: #3a3a3a;
}
```

**Color application:**
All existing color values in `styles.css` must be replaced with CSS variables:
- `background: #ffffff` → `background: var(--bg-primary)`
- `color: #2c3e50` → `color: var(--text-primary)`
- `border: 1px solid #dee2e6` → `border: 1px solid var(--border)`

#### Theme Toggle UI

**Location:** Header, right side (next to search bar)

**HTML Structure:**
```html
<header class="header">
  <h1 class="header-title">Qontract Schema Viewer</h1>
  <div class="header-controls">
    <div class="search-container">
      <input type="text" id="searchInput" class="search-input" placeholder="Search schemas...">
      <button id="searchClear" class="search-clear">×</button>
    </div>
    <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
      <span class="theme-icon">☀️</span>
      <span class="theme-label">Light</span>
    </button>
  </div>
</header>
```

**Toggle button states:**
- Light mode: `☀️ Light` (sun icon)
- Dark mode: `🌙 Dark` (moon icon)

**Toggle behavior:**
```javascript
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  // Apply theme
  document.documentElement.setAttribute('data-theme', newTheme);
  
  // Update button
  const icon = newTheme === 'dark' ? '🌙' : '☀️';
  const label = newTheme === 'dark' ? 'Dark' : 'Light';
  document.querySelector('.theme-icon').textContent = icon;
  document.querySelector('.theme-label').textContent = label;
  
  // Save preference
  localStorage.setItem('theme', newTheme);
}
```

**Initial theme detection:**
```javascript
function initTheme() {
  // Check localStorage first
  let theme = localStorage.getItem('theme');
  
  // Fall back to system preference
  if (!theme) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    theme = prefersDark ? 'dark' : 'light';
  }
  
  // Apply theme
  document.documentElement.setAttribute('data-theme', theme);
  
  // Update button
  const icon = theme === 'dark' ? '🌙' : '☀️';
  const label = theme === 'dark' ? 'Dark' : 'Light';
  document.querySelector('.theme-icon').textContent = icon;
  document.querySelector('.theme-label').textContent = label;
}

// Call on page load (in init() function)
initTheme();
```

**Why auto-detect:** Respects user's system preference out-of-the-box, matching modern web app patterns (GitHub, VS Code, etc.). Users who prefer a different theme can override with the toggle.

### 2. Single-Page Layout (No Tabs)

#### Current State (Tabs)

The existing implementation uses tab navigation:
```html
<div class="tabs">
  <div class="tab active">Properties</div>
  <div class="tab">Dependencies</div>
</div>
<div class="tab-content active" id="properties-tab">...</div>
<div class="tab-content" id="dependencies-tab">...</div>
```

JavaScript manages tab switching via `switchTab()` function and `state.activeTab`.

#### New State (Side-by-Side)

**Remove:**
- `.tabs` container and tab buttons
- `switchTab()` function
- `state.activeTab` property
- `.tab-content` wrappers and `.active` class toggling

**Add:**
- Two-column flex layout with explicit sections
- Section headers with visual distinction

**HTML Structure:**
```html
<div class="schema-content">
  <section class="properties-section">
    <h3 class="section-header properties-header">Properties</h3>
    <table class="properties-table">...</table>
  </section>
  
  <section class="dependencies-section">
    <h3 class="section-header dependencies-header">Dependencies</h3>
    <div class="dependencies-stats">...</div>
    <div class="dependencies-tree">...</div>
  </section>
</div>
```

#### CSS Layout

**Desktop (side-by-side, 60/40 split):**
```css
.schema-content {
  display: flex;
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.properties-section {
  flex: 3; /* 60% */
  min-width: 0; /* Allow table to shrink */
}

.dependencies-section {
  flex: 2; /* 40% */
  border-left: 2px solid var(--border);
  padding-left: 1.5rem;
}

.section-header {
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.properties-header {
  border-bottom: 2px solid var(--primary);
}

.dependencies-header {
  border-bottom: 2px solid var(--success);
}
```

**Mobile (vertical stack, < 768px):**
```css
@media (max-width: 768px) {
  .schema-content {
    flex-direction: column;
  }
  
  .dependencies-section {
    border-left: none;
    border-top: 2px solid var(--border);
    padding-left: 0;
    padding-top: 1.5rem;
    margin-top: 1.5rem;
  }
}
```

#### JavaScript Changes

**Modified function: `loadSchema()`**
```javascript
function loadSchema(schemaPath) {
  const schema = state.data.schemas.find(s => s.path === schemaPath);
  if (!schema) return;
  
  state.currentSchema = schema;
  const mainPanel = document.getElementById('mainPanel');
  
  // Schema header
  const header = document.createElement('div');
  header.className = 'schema-header';
  header.innerHTML = `
    <h2 class="schema-title">${schema.name}</h2>
    <div class="schema-meta">
      <span class="schema-path">${schema.path}</span>
    </div>
  `;
  
  // REMOVED: Tab navigation container and tab buttons
  // REMOVED: Tab content wrappers
  
  // NEW: Single content container with both sections
  const contentContainer = document.createElement('div');
  contentContainer.className = 'schema-content';
  
  // Properties section
  const propertiesSection = document.createElement('section');
  propertiesSection.className = 'properties-section';
  propertiesSection.innerHTML = '<h3 class="section-header properties-header">Properties</h3>';
  propertiesSection.appendChild(renderPropertiesTable());
  
  // Dependencies section
  const dependenciesSection = document.createElement('section');
  dependenciesSection.className = 'dependencies-section';
  dependenciesSection.innerHTML = '<h3 class="section-header dependencies-header">Dependencies</h3>';
  dependenciesSection.appendChild(renderDependenciesTree());
  
  contentContainer.appendChild(propertiesSection);
  contentContainer.appendChild(dependenciesSection);
  
  // Build main panel
  mainPanel.innerHTML = '';
  mainPanel.appendChild(header);
  mainPanel.appendChild(contentContainer);
  
  // Update sidebar focus (see section 3)
  updateSidebarFocus(schemaPath);
}
```

**Removed functions:**
- `switchTab(tabName)` - no longer needed

**Renamed functions (for clarity):**
- `renderPropertiesTab()` → `renderPropertiesTable()` (returns just the table element)
- `renderDependenciesTab()` → `renderDependenciesTree()` (returns tree container)

**Why side-by-side:** User feedback indicated frustration with tab switching when cross-referencing properties and dependencies. Side-by-side layout allows viewing both sections simultaneously on desktop screens while gracefully degrading to vertical stack on mobile.

### 3. Sidebar Auto-Focus on Dependency Click

#### Current Behavior

When user clicks a dependency link (e.g., "→ product-1.yml"), the `loadSchema()` function loads the target schema and updates the main panel. However, the sidebar does not update to highlight the newly loaded schema.

#### New Behavior

After clicking a dependency link, the sidebar should:
1. **Expand category** (if collapsed) containing the target schema
2. **Highlight** the target schema item with active state
3. **Scroll** the target schema item into view
4. **Animate** a brief pulse effect to draw attention

#### Implementation

**Function: `updateSidebarFocus(schemaPath)`**

Called at the end of `loadSchema()` to synchronize sidebar state with loaded schema.

```javascript
function updateSidebarFocus(schemaPath) {
  // Remove old active state
  document.querySelectorAll('.schema-item.active').forEach(el => {
    el.classList.remove('active', 'sidebar-highlight');
  });
  
  // Find target schema item
  const schemaItem = document.querySelector(`[data-schema-path="${schemaPath}"]`);
  if (!schemaItem) return;
  
  // Expand parent category if collapsed
  const category = schemaItem.closest('.category');
  if (category) {
    const categoryHeader = category.querySelector('.category-header');
    const isCollapsed = categoryHeader.querySelector('.category-toggle').textContent === '▶';
    
    if (isCollapsed) {
      // Simulate click to expand
      categoryHeader.click();
    }
  }
  
  // Apply active state and highlight animation
  schemaItem.classList.add('active', 'sidebar-highlight');
  
  // Scroll into view (centered in sidebar)
  schemaItem.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });
  
  // Remove highlight animation after 1 second
  setTimeout(() => {
    schemaItem.classList.remove('sidebar-highlight');
  }, 1000);
}
```

**Modified function: `loadSchema()`**

Add call to `updateSidebarFocus()` at the end:

```javascript
function loadSchema(schemaPath) {
  // ... existing schema loading logic ...
  
  // Update sidebar focus (NEW)
  updateSidebarFocus(schemaPath);
}
```

**CSS: Highlight Animation**

```css
/* Active state (persistent) */
.schema-item.active {
  background: var(--primary);
  color: white;
  font-weight: 500;
}

/* Highlight animation (temporary) */
.sidebar-highlight {
  animation: pulse 1s ease-out;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.4);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 123, 255, 0);
  }
}

/* Dark mode pulse (different color) */
[data-theme="dark"] .sidebar-highlight {
  animation: pulse-dark 1s ease-out;
}

@keyframes pulse-dark {
  0% {
    box-shadow: 0 0 0 0 rgba(100, 181, 246, 0.5);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(100, 181, 246, 0.4);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(100, 181, 246, 0);
  }
}
```

**Dependency Link Click Handling**

Dependency links already call `loadSchema()` via onclick handlers in the existing implementation:

```javascript
// In renderDependenciesTree()
const link = document.createElement('a');
link.href = '#';
link.className = 'schema-link';
link.textContent = `→ ${dep.target}`;
link.onclick = (e) => {
  e.preventDefault();
  loadSchema(dep.targetPath);
};
```

No changes needed to link rendering - `updateSidebarFocus()` is automatically called via `loadSchema()`.

**Why auto-focus:** Improves navigation UX by providing visual feedback that the clicked link actually loaded. Users can see where they are in the schema hierarchy without manually searching the sidebar.

## Testing Strategy

**Manual Testing Checklist:**

1. **Dark Mode:**
   - [ ] Light mode displays correctly on page load (system theme = light)
   - [ ] Dark mode displays correctly on page load (system theme = dark)
   - [ ] Theme toggle button switches themes correctly
   - [ ] Theme preference persists after page reload
   - [ ] All UI elements are readable in both themes (no contrast issues)
   - [ ] Type badges, borders, and backgrounds use correct theme colors

2. **Single-Page Layout:**
   - [ ] Properties and Dependencies sections display side-by-side on desktop (> 768px)
   - [ ] Sections stack vertically on mobile (< 768px)
   - [ ] Both sections are visible without scrolling (on schemas with few properties)
   - [ ] Scrolling works correctly when content overflows
   - [ ] Section headers are visually distinct (blue vs. green borders)
   - [ ] No UI elements are hidden or overlapping

3. **Sidebar Auto-Focus:**
   - [ ] Clicking a dependency link loads the target schema
   - [ ] Sidebar highlights the newly loaded schema
   - [ ] Collapsed categories expand when target schema is inside
   - [ ] Sidebar scrolls to bring highlighted schema into view
   - [ ] Pulse animation plays for 1 second
   - [ ] Active highlight persists until different schema is clicked
   - [ ] Works correctly when clicking dependencies from different schemas

4. **Regression Testing:**
   - [ ] Search functionality still works
   - [ ] Category collapse/expand still works
   - [ ] Clicking sidebar schemas still works
   - [ ] Properties table rendering is unchanged
   - [ ] Dependencies tree rendering is unchanged
   - [ ] Mobile responsiveness is preserved

**Browser Testing:**
- Chrome/Chromium (primary)
- Firefox
- Safari (if available)
- Mobile browsers (responsive design mode)

**No automated tests needed:** This is a static site with pure client-side JavaScript. Manual testing is sufficient for UI changes.

## Deployment

**Process:**
1. Modify `scripts/templates/index.html` and `scripts/templates/styles.css`
2. Run `make generate-docs` to regenerate `docs/` with updated templates
3. Test locally by opening `docs/index.html` in browser
4. Commit changes to both `scripts/templates/` and `docs/` directories
5. Push to GitHub - GitHub Pages automatically deploys from `docs/`

**Files Modified:**
- `scripts/templates/index.html` (~850 lines after changes)
- `scripts/templates/styles.css` (~600 lines after changes)

**Generated Files Updated:**
- `docs/index.html` (copy of template)
- `docs/styles.css` (copy of template)

**No Python Changes:** The generator script (`scripts/generate_schema_docs.py`) does not need modification - it already copies template files to `docs/`.

## Success Criteria

1. **Dark mode functional:** Theme toggle works, preference persists, all colors adapt correctly
2. **Layout improved:** Properties and Dependencies visible together on desktop, stack gracefully on mobile
3. **Navigation enhanced:** Sidebar highlights and scrolls to focused schema when dependency clicked
4. **No regressions:** All existing functionality (search, categories, navigation) works as before
5. **Accessibility maintained:** Keyboard navigation, ARIA labels, and color contrast remain compliant

## Future Enhancements (Out of Scope)

- Keyboard shortcuts for theme toggle
- Three-state theme selector (light/dark/auto with explicit indicator)
- Collapsible properties/dependencies sections
- Sticky section headers when scrolling
- Dark mode syntax highlighting for code snippets (if added later)

These improvements are left for future iterations to keep this change focused and low-risk.

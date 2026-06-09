# Schema Viewer UI Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dark mode toggle, side-by-side layout (no tabs), and sidebar auto-focus to the existing schema viewer

**Architecture:** Modify two existing template files (`scripts/templates/index.html` and `scripts/templates/styles.css`) with incremental changes. No new files, no Python generator changes.

**Tech Stack:** Vanilla JavaScript (ES6+), CSS3 with variables, HTML5

---

## File Structure

**Modified Files:**
- `scripts/templates/styles.css` - Add CSS variables for dark mode, side-by-side layout styles, pulse animation
- `scripts/templates/index.html` - Add theme toggle button and JavaScript, remove tab logic, add sidebar focus function

**Generated Files (auto-updated by `make generate-docs`):**
- `docs/index.html` - Copy of template
- `docs/styles.css` - Copy of template

---

### Task 1: Add Dark Mode CSS Variables

**Files:**
- Modify: `scripts/templates/styles.css:8-18`

- [ ] **Step 1: Expand existing CSS variables in `:root` selector**

Replace the existing `:root` block (lines 8-18) with expanded light mode variables:

```css
:root {
    /* Semantic colors (keep existing) */
    --primary: #007bff;
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    
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
    
    /* Type badges */
    --type-string-bg: #e9ecef;
    --type-enum-bg: #fff3cd;
    --type-ref-bg: #d4edff;
    --type-array-bg: #e7f3ff;
    --type-object-bg: #f8f9fa;
    
    /* Legacy variables (for compatibility) */
    --bg-light: #f8f9fa;
    --bg-secondary: #e9ecef;
    --text-dark: #2c3e50;
}
```

- [ ] **Step 2: Add dark mode CSS variables**

After the `:root` block, add:

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
    
    /* Type badges */
    --type-string-bg: #3a3a3a;
    --type-enum-bg: #4a4a2d;
    --type-ref-bg: #2d3a4a;
    --type-array-bg: #2d3a4a;
    --type-object-bg: #3a3a3a;
    
    /* Legacy variables */
    --bg-light: #2d2d2d;
    --text-dark: #e0e0e0;
}
```

- [ ] **Step 3: Commit CSS variables**

```bash
git add scripts/templates/styles.css
git commit -m "feat: add dark mode CSS variables

Add comprehensive CSS variable definitions for light and dark themes.
Light theme variables in :root, dark theme overrides in [data-theme=dark].

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Convert Hardcoded Colors to CSS Variables

**Files:**
- Modify: `scripts/templates/styles.css` (entire file)

- [ ] **Step 1: Replace body background**

Find line ~24:
```css
background: #ffffff;
```

Replace with:
```css
background: var(--bg-primary);
```

- [ ] **Step 2: Replace header background**

Find line ~46:
```css
background: var(--text-dark);
```

Replace with:
```css
background: var(--header-bg);
```

- [ ] **Step 3: Replace sidebar background**

Find the `.sidebar` selector and change:
```css
background: #f8f9fa;
```

To:
```css
background: var(--bg-secondary);
```

- [ ] **Step 4: Replace border colors throughout**

Search for all instances of `#dee2e6` and replace with `var(--border)`.
Search for all instances of `#e9ecef` (used as borders) and replace with `var(--border-light)`.

- [ ] **Step 5: Replace text colors**

Search for `#2c3e50` and replace with `var(--text-primary)`.
Search for `#666` or `#666666` and replace with `var(--text-secondary)`.
Search for `#999` or `#999999` and replace with `var(--text-muted)`.

- [ ] **Step 6: Replace background colors**

Search for `#f8f9fa` and replace with `var(--bg-secondary)`.
Search for `#e9ecef` (used as backgrounds) and replace with `var(--bg-tertiary)`.
Search for `#ffffff` and replace with `var(--bg-primary)`.

- [ ] **Step 7: Test color replacements**

Open `scripts/templates/styles.css` and verify:
- No hardcoded hex colors remain except in type badge classes
- All replaced colors use CSS variables
- Type badge colors use `--type-*-bg` variables

Expected: All colors are now theme-aware

- [ ] **Step 8: Commit color variable migration**

```bash
git add scripts/templates/styles.css
git commit -m "refactor: migrate hardcoded colors to CSS variables

Replace all hardcoded hex colors with CSS variables for theme support.
Backgrounds, text, borders now use var() references.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Add Theme Toggle Button to HTML

**Files:**
- Modify: `scripts/templates/index.html:18-24`

- [ ] **Step 1: Wrap search bar in header-controls container**

Find the header section (around line 18):
```html
<header class="header">
    <h1 class="header-title">Qontract Schema Viewer</h1>
    <div class="search-container">
        <input type="text" id="searchInput" class="search-input" placeholder="Search schemas...">
        <button id="searchClear" class="search-clear" style="display: none;">×</button>
    </div>
</header>
```

Replace with:
```html
<header class="header">
    <h1 class="header-title">Qontract Schema Viewer</h1>
    <div class="header-controls">
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Search schemas...">
            <button id="searchClear" class="search-clear" style="display: none;">×</button>
        </div>
        <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
            <span class="theme-icon">☀️</span>
            <span class="theme-label">Light</span>
        </button>
    </div>
</header>
```

- [ ] **Step 2: Commit HTML structure change**

```bash
git add scripts/templates/index.html
git commit -m "feat: add theme toggle button to header

Wrap search and theme toggle in header-controls container.
Button shows icon (☀️/🌙) and label (Light/Dark).

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Add Theme Toggle CSS Styles

**Files:**
- Modify: `scripts/templates/styles.css` (after header styles)

- [ ] **Step 1: Add header-controls flexbox styles**

Find the header styles section and add after `.search-container`:

```css
.header-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
}
```

- [ ] **Step 2: Add theme toggle button styles**

```css
.theme-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s, border-color 0.2s;
}

.theme-toggle:hover {
    background: var(--bg-secondary);
    border-color: var(--primary);
}

.theme-icon {
    font-size: 1.2rem;
    line-height: 1;
}

.theme-label {
    font-weight: 500;
}
```

- [ ] **Step 3: Update mobile responsive styles**

Find the mobile media query (`@media (max-width: 768px)`) and add:

```css
@media (max-width: 768px) {
    .header-controls {
        flex-direction: column;
        align-items: stretch;
        gap: 0.5rem;
        width: 100%;
    }
    
    .search-container {
        width: 100%;
    }
    
    .theme-toggle {
        width: 100%;
        justify-content: center;
    }
}
```

- [ ] **Step 4: Commit theme toggle styles**

```bash
git add scripts/templates/styles.css
git commit -m "style: add theme toggle button styles

Add flexbox layout for header-controls and theme-toggle button.
Mobile responsive with vertical stacking.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Implement Theme Toggle JavaScript

**Files:**
- Modify: `scripts/templates/index.html` (in `<script>` section)

- [ ] **Step 1: Add initTheme() function**

Add this function after the `init()` function:

```javascript
/**
 * Initialize theme based on localStorage or system preference.
 */
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
    
    // Update button (if it exists - may not on first load)
    const iconEl = document.querySelector('.theme-icon');
    const labelEl = document.querySelector('.theme-label');
    if (iconEl && labelEl) {
        const icon = theme === 'dark' ? '🌙' : '☀️';
        const label = theme === 'dark' ? 'Dark' : 'Light';
        iconEl.textContent = icon;
        labelEl.textContent = label;
    }
}
```

- [ ] **Step 2: Add toggleTheme() function**

Add this function after `initTheme()`:

```javascript
/**
 * Toggle between light and dark themes.
 */
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

- [ ] **Step 3: Call initTheme() in init() function**

Find the `init()` function and add `initTheme();` at the very beginning (before loading schemas.json):

```javascript
async function init() {
    // Initialize theme first
    initTheme();
    
    try {
        // Load schemas.json
        const response = await fetch('schemas.json');
        // ... rest of init code
    }
}
```

- [ ] **Step 4: Add event listener for theme toggle button**

Find the `setupEventListeners()` function and add:

```javascript
// Theme toggle
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
```

- [ ] **Step 5: Commit theme toggle JavaScript**

```bash
git add scripts/templates/index.html
git commit -m "feat: implement theme toggle JavaScript

Add initTheme() and toggleTheme() functions.
Auto-detect system preference on first load.
Persist theme choice to localStorage.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Remove Tab Navigation CSS

**Files:**
- Modify: `scripts/templates/styles.css`

- [ ] **Step 1: Remove .tabs styles**

Find and delete the `.tabs` CSS block (search for `.tabs {`):

```css
/* DELETE THIS ENTIRE BLOCK */
.tabs {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}

.tab {
    padding: 0.75rem 1.5rem;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: border-color 0.2s, color 0.2s;
    color: var(--text-secondary);
}

.tab:hover {
    color: var(--text-primary);
}

.tab.active {
    border-bottom-color: var(--primary);
    color: var(--text-primary);
    font-weight: 500;
}
```

- [ ] **Step 2: Remove .tab-content styles**

Find and delete the `.tab-content` CSS block:

```css
/* DELETE THIS ENTIRE BLOCK */
.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}
```

- [ ] **Step 3: Commit tab CSS removal**

```bash
git add scripts/templates/styles.css
git commit -m "refactor: remove tab navigation CSS

Remove .tabs and .tab-content styles (replaced with side-by-side layout).

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Add Side-by-Side Layout CSS

**Files:**
- Modify: `scripts/templates/styles.css`

- [ ] **Step 1: Add schema-content layout styles**

Add these styles in the main panel section (after `.schema-header`):

```css
/* Schema content (side-by-side layout) */
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
```

- [ ] **Step 2: Add section header styles**

```css
.section-header {
    margin: 0 0 1rem 0;
    padding-bottom: 0.5rem;
    font-size: 1.1rem;
    color: var(--text-primary);
    font-weight: 600;
}

.properties-header {
    border-bottom: 2px solid var(--primary);
}

.dependencies-header {
    border-bottom: 2px solid var(--success);
}
```

- [ ] **Step 3: Add mobile responsive layout**

Find the mobile media query and add:

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

- [ ] **Step 4: Commit side-by-side layout CSS**

```bash
git add scripts/templates/styles.css
git commit -m "feat: add side-by-side layout CSS

Add flexbox layout for properties and dependencies sections.
60/40 split on desktop, vertical stack on mobile.
Section headers with colored borders (blue/green).

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Remove Tab Navigation JavaScript

**Files:**
- Modify: `scripts/templates/index.html` (in `<script>` section)

- [ ] **Step 1: Remove state.activeTab property**

Find the `state` object definition and remove the `activeTab` line:

```javascript
const state = {
    data: null,
    currentSchema: null,
    searchQuery: '',
    filteredSchemas: [],
    debounceTimer: null
    // REMOVE: activeTab: 'properties'
};
```

- [ ] **Step 2: Remove switchTab() function**

Find and delete the entire `switchTab()` function:

```javascript
// DELETE THIS ENTIRE FUNCTION
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tabs .tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}
```

- [ ] **Step 3: Commit tab JavaScript removal**

```bash
git add scripts/templates/index.html
git commit -m "refactor: remove tab navigation JavaScript

Remove state.activeTab and switchTab() function.
Replaced with side-by-side layout rendering.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 9: Update loadSchema() for Side-by-Side Layout

**Files:**
- Modify: `scripts/templates/index.html` (loadSchema function)

- [ ] **Step 1: Refactor loadSchema() to remove tab rendering**

Find the `loadSchema()` function and replace the section that creates tabs with the new side-by-side layout. Replace this:

```javascript
// OLD CODE - DELETE THIS:
// Create tab navigation
const tabsContainer = document.createElement('div');
tabsContainer.className = 'tabs';

const propertiesTab = document.createElement('div');
propertiesTab.className = 'tab active';
propertiesTab.textContent = 'Properties';
propertiesTab.addEventListener('click', () => switchTab('properties'));

const dependenciesTab = document.createElement('div');
dependenciesTab.className = 'tab';
dependenciesTab.textContent = 'Dependencies';
dependenciesTab.addEventListener('click', () => switchTab('dependencies'));

tabsContainer.appendChild(propertiesTab);
tabsContainer.appendChild(dependenciesTab);

// Create tab content containers
const propertiesContent = document.createElement('div');
propertiesContent.id = 'properties-tab';
propertiesContent.className = 'tab-content active';
propertiesContent.appendChild(renderPropertiesTab());

const dependenciesContent = document.createElement('div');
dependenciesContent.id = 'dependencies-tab';
dependenciesContent.className = 'tab-content';
dependenciesContent.appendChild(renderDependenciesTab());

// Build main panel
mainPanel.innerHTML = '';
mainPanel.appendChild(header);
mainPanel.appendChild(tabsContainer);
mainPanel.appendChild(propertiesContent);
mainPanel.appendChild(dependenciesContent);
```

With this NEW CODE:

```javascript
// NEW CODE - side-by-side layout
const contentContainer = document.createElement('div');
contentContainer.className = 'schema-content';

// Properties section
const propertiesSection = document.createElement('section');
propertiesSection.className = 'properties-section';
const propertiesHeader = document.createElement('h3');
propertiesHeader.className = 'section-header properties-header';
propertiesHeader.textContent = 'Properties';
propertiesSection.appendChild(propertiesHeader);
propertiesSection.appendChild(renderPropertiesTab());

// Dependencies section
const dependenciesSection = document.createElement('section');
dependenciesSection.className = 'dependencies-section';
const dependenciesHeader = document.createElement('h3');
dependenciesHeader.className = 'section-header dependencies-header';
dependenciesHeader.textContent = 'Dependencies';
dependenciesSection.appendChild(dependenciesHeader);
dependenciesSection.appendChild(renderDependenciesTab());

contentContainer.appendChild(propertiesSection);
contentContainer.appendChild(dependenciesSection);

// Build main panel
mainPanel.innerHTML = '';
mainPanel.appendChild(header);
mainPanel.appendChild(contentContainer);
```

- [ ] **Step 2: Commit loadSchema() refactor**

```bash
git add scripts/templates/index.html
git commit -m "refactor: update loadSchema() for side-by-side layout

Remove tab container and tab content wrappers.
Render properties and dependencies sections side-by-side.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Add Sidebar Auto-Focus CSS

**Files:**
- Modify: `scripts/templates/styles.css`

- [ ] **Step 1: Update .schema-item.active styles**

Find the `.schema-item` styles and ensure the `.active` state is defined:

```css
.schema-item.active {
    background: var(--primary);
    color: white;
    font-weight: 500;
}
```

- [ ] **Step 2: Add pulse animation**

Add at the end of the CSS file:

```css
/* Sidebar highlight animation */
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

- [ ] **Step 3: Commit sidebar highlight animation**

```bash
git add scripts/templates/styles.css
git commit -m "feat: add sidebar highlight pulse animation

Add pulse keyframes for both light and dark themes.
Temporary 1-second animation when schema is focused.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 11: Implement updateSidebarFocus() Function

**Files:**
- Modify: `scripts/templates/index.html` (in `<script>` section)

- [ ] **Step 1: Add updateSidebarFocus() function**

Add this function after the `loadSchema()` function:

```javascript
/**
 * Update sidebar to highlight and scroll to the currently loaded schema.
 * Expands parent category if collapsed.
 * 
 * @param {string} schemaPath - Path of the schema to focus (e.g., "app-sre/app-1.yml")
 */
function updateSidebarFocus(schemaPath) {
    // Remove old active state and highlight
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
        const toggleIcon = categoryHeader.querySelector('.category-toggle');
        const isCollapsed = toggleIcon.textContent.trim() === '▶';
        
        if (isCollapsed) {
            // Simulate click to expand category
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

- [ ] **Step 2: Call updateSidebarFocus() from loadSchema()**

Find the end of the `loadSchema()` function (after appending to mainPanel) and add:

```javascript
// Update sidebar focus
updateSidebarFocus(schemaPath);
```

The end of `loadSchema()` should now look like:

```javascript
    // Build main panel
    mainPanel.innerHTML = '';
    mainPanel.appendChild(header);
    mainPanel.appendChild(contentContainer);
    
    // Update sidebar focus
    updateSidebarFocus(schemaPath);
}
```

- [ ] **Step 3: Commit sidebar auto-focus function**

```bash
git add scripts/templates/index.html
git commit -m "feat: implement sidebar auto-focus on navigation

Add updateSidebarFocus() function to highlight and scroll to active schema.
Auto-expands collapsed categories.
Pulse animation for visual feedback.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 12: Regenerate Documentation and Test

**Files:**
- Generate: `docs/index.html`
- Generate: `docs/styles.css`

- [ ] **Step 1: Regenerate documentation**

Run the generator to copy templates to docs/:

```bash
make generate-docs
```

Expected: Templates copied to docs/, schemas.json regenerated

- [ ] **Step 2: Open viewer in browser (light mode)**

```bash
# Open in default browser
xdg-open docs/index.html 2>/dev/null || open docs/index.html || start docs/index.html
```

Expected: Page loads in light mode (or dark mode if system preference is dark)

- [ ] **Step 3: Test dark mode toggle**

Manual steps:
1. Click theme toggle button
2. Verify page switches to dark mode
3. Check all UI elements are readable
4. Reload page
5. Verify theme persists

Expected: Theme switches correctly, persists across reloads

- [ ] **Step 4: Test side-by-side layout (desktop)**

Manual steps:
1. Resize browser to > 768px width
2. Click a schema in sidebar
3. Verify Properties and Dependencies sections appear side-by-side
4. Verify 60/40 split (properties wider)

Expected: Both sections visible simultaneously

- [ ] **Step 5: Test mobile layout**

Manual steps:
1. Resize browser to < 768px width (or use responsive design mode)
2. Click a schema
3. Verify Properties section appears first
4. Scroll down
5. Verify Dependencies section appears below

Expected: Vertical stack on narrow screens

- [ ] **Step 6: Test sidebar auto-focus**

Manual steps:
1. Load a schema with dependencies (e.g., app-sre/app-1.yml)
2. Click a dependency link in the Dependencies section
3. Verify sidebar highlights the target schema
4. Verify pulse animation plays
5. Verify collapsed categories expand automatically

Expected: Sidebar updates and scrolls to focused schema

- [ ] **Step 7: Test regression - search**

Manual steps:
1. Type "app" in search bar
2. Verify schemas filter correctly
3. Click filtered schema
4. Verify it loads

Expected: Search still works

- [ ] **Step 8: Test regression - category collapse**

Manual steps:
1. Click category header to collapse
2. Verify schemas hide
3. Click again to expand
4. Verify schemas show

Expected: Category collapse still works

- [ ] **Step 9: Commit generated files**

```bash
git add docs/index.html docs/styles.css
git commit -m "build: regenerate docs with UI improvements

Regenerate viewer with dark mode, side-by-side layout, sidebar auto-focus.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 13: Final Testing and Documentation

**Files:**
- Modify: `README.md` (optional - document new features)

- [ ] **Step 1: Test all browsers**

Test in available browsers:
- Chrome/Chromium
- Firefox
- Safari (if available)

Expected: All features work in all browsers

- [ ] **Step 2: Test theme preference edge cases**

Manual steps:
1. Clear localStorage: `localStorage.clear()`
2. Reload page with light system theme
3. Verify starts in light mode
4. Clear localStorage again
5. Change system to dark theme
6. Reload page
7. Verify starts in dark mode

Expected: Auto-detects system preference correctly

- [ ] **Step 3: Test sidebar focus edge cases**

Manual steps:
1. Load schema from collapsed category
2. Click dependency in different collapsed category
3. Verify both categories expand as needed
4. Click dependency to same schema (self-reference)
5. Verify no errors

Expected: Handles all navigation scenarios gracefully

- [ ] **Step 4: Update README (optional)**

If README.md mentions the viewer, add a note about new features:

```markdown
### Schema Documentation

The schema viewer now includes:
- **Dark mode**: Auto-detects system preference, manual toggle available
- **Side-by-side layout**: View properties and dependencies simultaneously
- **Smart navigation**: Clicking dependencies auto-focuses sidebar
```

- [ ] **Step 5: Final commit (if README updated)**

```bash
git add README.md
git commit -m "docs: update README with new viewer features

Document dark mode, side-by-side layout, and sidebar auto-focus.

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Verify all tests passed**

Review manual testing checklist from spec (section "Testing Strategy"):

Dark Mode:
- [x] Light mode displays correctly
- [x] Dark mode displays correctly
- [x] Theme toggle switches themes
- [x] Theme preference persists
- [x] All UI elements readable in both themes
- [x] Type badges use correct theme colors

Single-Page Layout:
- [x] Side-by-side on desktop
- [x] Vertical stack on mobile
- [x] Both sections visible without scrolling
- [x] Scrolling works when content overflows
- [x] Section headers visually distinct
- [x] No hidden/overlapping elements

Sidebar Auto-Focus:
- [x] Clicking dependency loads target schema
- [x] Sidebar highlights newly loaded schema
- [x] Collapsed categories expand
- [x] Sidebar scrolls to highlighted schema
- [x] Pulse animation plays for 1 second
- [x] Active highlight persists
- [x] Works from different schemas

Regression Testing:
- [x] Search functionality works
- [x] Category collapse/expand works
- [x] Clicking sidebar schemas works
- [x] Properties table rendering unchanged
- [x] Dependencies tree rendering unchanged
- [x] Mobile responsiveness preserved

Expected: All checklist items verified

---

## Self-Review

**Spec coverage check:**
- [x] Dark mode CSS variables (Task 1) → Spec section 1, CSS Variables Structure
- [x] Color migration to CSS variables (Task 2) → Spec section 1, Color application
- [x] Theme toggle button HTML (Task 3) → Spec section 1, Theme Toggle UI
- [x] Theme toggle CSS (Task 4) → Spec section 1, Theme Toggle UI
- [x] Theme toggle JavaScript (Task 5) → Spec section 1, Toggle behavior & Initial theme detection
- [x] Remove tab CSS (Task 6) → Spec section 2, Remove
- [x] Add side-by-side CSS (Task 7) → Spec section 2, CSS Layout
- [x] Remove tab JavaScript (Task 8) → Spec section 2, Remove
- [x] Update loadSchema() (Task 9) → Spec section 2, JavaScript Changes
- [x] Sidebar highlight CSS (Task 10) → Spec section 3, CSS: Highlight Animation
- [x] updateSidebarFocus() function (Task 11) → Spec section 3, Function: updateSidebarFocus()
- [x] Testing (Task 12-13) → Spec Testing Strategy section

All spec requirements covered.

**Placeholder scan:**
No TBD, TODO, or placeholders. All code blocks are complete and executable.

**Type consistency:**
- Function names: `initTheme()`, `toggleTheme()`, `updateSidebarFocus()`, `loadSchema()`
- CSS classes: `.theme-toggle`, `.schema-content`, `.properties-section`, `.dependencies-section`, `.sidebar-highlight`
- Data attributes: `data-theme`, `data-schema-path`

All names consistent across tasks.

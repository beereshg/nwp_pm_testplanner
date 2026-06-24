---
name: nwp-tcd-description
description: >
  Generate, preview, and update NWP PM Test Case Definition (TCD) descriptions.
  Reads TCD from HSD, enriches Feature Overview from HAS/MAS/KB, caches in
  KB/pm_tcd_kb, previews as HTML in tcd_description_output/, and updates HSD
  only after explicit user confirmation. Use when: enriching a TCD description,
  updating Feature Overview from specs, or generating TCD preview HTML.
---

# NWP TCD Description Skill

> Repo root: `c:/github/nwp_testplan/`
> Depends on: `nwp-tc-deepanalysis` skill (NWP architecture constants, ZBB table, HSD API patterns)

---

## When to Use

- User provides a TCD ID and asks to enrich, update, or preview its description
- Feature Overview in a TCD is generic (no register paths, no HAS refs)
- User wants to see what a TCD description looks like before pushing to HSD
- User says `update TCD <ID>`, `preview TCD <ID>`, `enrich TCD <ID>`

---

## Workflow

`
Step 1: Fetch       HSD TCD → KB/pm_tcd_kb cache (.md)
Step 2: Enrich      HAS/MAS/KB → improve Feature Overview in cache file
Step 3: Preview     cache → tcd_description_output/TCD_{id}_{slug}_preview.html
Step 4: Confirm     user reviews HTML preview
Step 5: Update HSD  PUT new description to HSD (only after confirmation)
`

**Never update HSD without explicit user confirmation after preview.**

---

## Step 1 — Fetch and Cache TCD

`python
from pathlib import Path
import sys, re
sys.path.insert(0, '.')
from hsd_utils import get_session, get_article, get_children

s = get_session()
TCD_ID = '<tcd_id>'

tcd = get_article(TCD_ID, fields='id,title,description,status,owner,parent_id', session=s)
tcs = get_children(TCD_ID, 'test_case',
    fields='id,title,status,test_case.val_environment,test_case.free_tag_1,test_case.free_tag_2',
    session=s)
`

**Cache file path:**
`KB/pm_tcd_kb/{tp_id}_{tp_slug}/TCD_{tcd_id}_{slug}.md`

Example: `KB/pm_tcd_kb/16030762839_sst_speed_select_technology/TCD_22022420855_pct_enabling_discovery.md`

---

## Step 2 — TCD KB File Format

Example path: `KB/pm_tcd_kb/15019477653_nwp_pm_socket_rapl/TCD_22022420798_socket_rapl_algorithm_functionality.md`

The KB file uses **8-section structure** matching the TCD description format. The generator
(`generate_tcd_preview.py`) renders all headings, tables, code blocks, and lists automatically.

### Section 1 Architecture — Supported Content Types

The generator renders Section 1 in order, separated by `### SubHeading` markers:

| Content Type | Markdown Syntax | Rendered As |
|-------------|-----------------|-------------|
| Intro paragraph | Plain text (no leading `#`, `|`, `-`, `*`, digit) | `<p>` with bold/code inline |
| Code block / ASCII diagram | ` ``` ... ``` ` | `<pre>` with blue left border |
| Table | `\| col \| col \|` rows | HTML table (separate per gap) |
| Bullet list | `- item` or `* item` | `<ul>` |
| Numbered list | `1. item`, `2. item` | `<ol>` |
| Sub-heading | `### Title` | `<h3>` — flushes pending table/list first |

**Key rules:**
- Two tables separated by a blank line (or `### SubHeading`) render as **two separate tables**
- `**bold**` and `` `code` `` in intro paragraphs render as `<strong>` and `<code>` (per-line conversion — no cross-line bold issues)
- `### Feature Overview` heading is **not needed** if the intro paragraph text is the feature overview — it would render as an empty h3
- Numbered list items must start with `\d+. ` or `\d+) ` pattern

### Recommended Section 1 Structure

```markdown
## Section 1: Architecture / Micro-architecture and Functionality

Intro paragraph with **bold** terms and `code` — no leading `### Feature Overview` needed.

### Runtime Control Flow

1. Step one description
2. Step two description

### Block Decomposition

` ` `
ASCII diagram here
` ` `

### Key Properties Table

| Property | Value A | Value B |
|----------|---------|---------|

### NWP-Specific Deltas

- Delta item 1
- Delta item 2

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [HSD ID — Title](url) | scenario | mechanism |
```

### Push to HSD — Extract desc-box only (skip header + TC table)

When pushing TCD preview HTML to HSD, extract only the `desc-box` div to start the
description from Section 1 (Architecture), skipping the preview header and TC summary table:

```python
import re
html = open('tcd_description_output/TCD_{id}_{slug}_preview.html', encoding='utf-8').read()
m = re.search(r'<div class="desc-box">(.*?)</div>\s*</div>\s*</body>', html, re.DOTALL)
content = m.group(1).strip() if m else html
# Then PUT content to HSD
```

### PowerShell heredoc warning

**Avoid** writing KB content via PowerShell heredoc (`@'...'@`) for lines with `**bold**`.
PowerShell can introduce extra `**` at line boundaries (e.g. `**text****` instead of `**text** `),
causing inverted bold in the rendered HTML. Prefer writing KB files directly via the `create_file`
tool or `replace_string_in_file`.



---

## Step 3 — Generate Preview HTML

**Simple header + description body — no sidebar.**

`powershell
# From repo root
python tools/html/generate_tcd_preview.py --tcd <TCD_ID> --force
# Output: tcd_description_output/TCD_{id}_{slug}_preview.html
`

**Preview HTML structure (lightweight):**
`html
<!-- Header bar: TCD title + metadata strip -->
<!-- Yellow notice: "Preview only — confirm before HSD update" -->
<!-- TC summary table (compact, single row per TC) -->
<!-- Description body (raw HSD HTML as-is) -->
`

No sidebar, no grid layout. Single-column, scrollable.

---

## Step 4 — User Reviews

User opens `tcd_description_output/TCD_{id}_{slug}_preview.html` and:
- Checks Feature Overview quality
- Checks register tables are accurate
- Checks NWP delta table
- Approves or requests changes

**Do not proceed to Step 5 without explicit approval.**

---

## Step 5 — Update HSD Description

Only after user confirms:

`python
import requests, urllib3
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
urllib3.disable_warnings()
s = requests.Session()
s.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
s.verify = False
s.headers.update({'Content-Type':'application/json','Accept':'application/json'})

r = s.put(f'https://hsdes-api.intel.com/rest/article/{TCD_ID}', json={
    'tenant': 'server',
    'subject': 'test_case_definition',
    'fieldValues': [{'description': NEW_HTML}, {'send_mail': 'false'}]
}, timeout=60)
print(r.status_code, 'OK' if r.status_code == 200 else r.text[:200])
`

**After update:** regenerate preview to confirm HSD shows new content.

---

## HSD Description HTML Format

Use the same section/box style as existing TCD descriptions:

`html
<div class="section" style="background:white;margin-bottom:25px;border-radius:10px;
     box-shadow:rgba(0,0,0,0.08) 0px 2px 10px;overflow:hidden;">
  <div class="section-header" style="background:rgb(0,113,197);color:white;
       padding:15px 25px;font-size:1.3em;font-weight:bold;">
    1. Architecture / Micro-architecture and Functionality
  </div>
  <div class="section-content" style="padding:25px;">
    <h3 style="color:rgb(0,113,197);border-bottom:2px solid rgb(0,113,197);
        padding-bottom:8px;margin-top:20px;">Feature Overview</h3>
    <!-- content -->
  </div>
</div>
`

**Section numbering convention:**
1. Architecture / Micro-architecture and Functionality  (Feature Overview, Enabling, Discovery, NWP Delta)
2. Interfaces and Protocols
3. Reset, Power, and Clocking
4. Programming Model
5. Operational Behavior  (Test Cases table)
6. Corner Cases & Error Handling
7. Security / Safety / Policy
8. References

---

## KB File Naming Convention

| Artifact | Path pattern |
|----------|-------------|
| TCD KB cache | `KB/pm_tcd_kb/{tp_id}_{tp_slug}/TCD_{tcd_id}_{slug}.md` |
| Preview HTML | `tcd_description_output/TCD_{tcd_id}_{slug}_preview.html` |
| KB feature ref | `KB/pm_features/{feature}/{subfeature}.md` |

**Slug:** title lowercased, spaces/special chars → `_`, max 50 chars.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Generic Feature Overview ("Validate X on NWP") | Replace with spec-derived content using HAS/MAS |
| Missing register paths | Read KB/pm_features article or query codesign-ask-specs-and-wikis |
| Updating HSD before preview | Always preview first, wait for confirm |
| HTML encoding issues | Use PowerShell heredoc (`@" ... "@`) for Python scripts |
| Wrong subject in PUT | Use `subject: test_case_definition` for TCD (not `test_case`) |

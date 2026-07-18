---
name: nwp-tcd-description
description: >
  Generate, preview, and update NWP PM Test Case Definition (TCD) descriptions.
  ID-driven and idempotent: given any TCD ID the skill resolves create-vs-refresh
  from filesystem + HSD state, always stops at the preview gate before pushing.
  Use when: enriching a TCD description, refreshing a cached KB file, previewing,
  or pushing an updated description to HSD.
---

# NWP TCD Description Skill

> Repo root: `c:/github/nwp_testplan/`
> Depends on: `nwp-tc-description` skill (NWP architecture constants, ZBB table, HSD API patterns)
> Related: `nwp-tpf-description` skill — architecture diagrams and feature-wide flows belong at TPF level, not in TCD Section 1
> Related: **`nwp-tc-description` skill** — HOW content (test steps, command lines, BIOS register execution sequences, measurement method) belongs in TC, not TCD. **The pass/fail bar (measurable thresholds, acceptance criteria) is owned by TCD §5.**

---

## When to Use

- User provides a **bare TCD ID** (e.g. `22022420855`) with no other context
- User says `enrich <ID>`, `refresh <ID>`, `regenerate <ID>`, `create description for <ID>`,
  `preview <ID>`, or `update <ID>`
- User wants to see a TCD description before pushing to HSD
- Feature Overview is generic; register paths or HAS refs are missing

The skill **infers create-vs-refresh from filesystem + HSD state**. The user never
has to specify which mode.

---

## Workflow — ID-Driven State Machine

The **only required input** is a TCD ID. The skill runs this state machine:

```
INPUT: TCD ID
  ↓
STEP 1 — RESOLVE STATE
  ↓
STEP 2 — SYNC KB (create or refresh)
  ↓
STEP 3 — GENERATE PREVIEW
  ↓
STEP 4 — ⚠️ MANDATORY REVIEW GATE (hard stop)
  ↓ (only after explicit “yes” to THIS preview)
STEP 5 — PUSH
```

**Hard rule:** HSD is never written before an explicit “yes” that follows
a preview generated in this session. A prior approval does not carry over
after any KB edit or regeneration.

---

## Step 1 — Resolve State

Given a TCD ID:

1. **Fetch live metadata from HSD** (source of truth):
   ```python
   from hsd_utils import get_session, get_article, get_children
   s = get_session()
   tcd = get_article(TCD_ID, fields='id,title,description,status,owner,parent_id', session=s)
   tcs  = get_children(TCD_ID, 'test_case',
       fields='id,title,status,test_case.val_environment,test_case.free_tag_1,test_case.free_tag_2',
       session=s)
   ```
   Derive canonical slug from live `tcd['title']`.

2. **Glob KB cache:** `KB/pm_tcd_kb/**/*{TCD_ID}*.md`

   | Result | Mode |
   |--------|------|
   | File found with matching slug | **REFRESH** |
   | File found with stale slug (HSD title changed) | Run *Stale KB File Handling* below, then **REFRESH** |
   | No file found | **CREATE** |

**Stale KB File Handling** (when glob finds ID but slug mismatch):
```powershell
# 1. Rename stale file to remove ID from glob path
Rename-Item 'KB/pm_tcd_kb/.../TCD_{id}_old_slug.md' 'TCD_STALE_old_slug_ref.md'
# 2. Add comment at top of stale file:
#    <!-- STALE: HSD {id} renamed. See TCD_{id}_{new_slug}.md -->
# 3. Proceed to CREATE mode with correct slug
```

---

## Step 2 — Sync KB

**CREATE mode:**
- Generate a new KB file at `KB/pm_tcd_kb/{tp_id}_{tp_slug}/TCD_{tcd_id}_{slug}.md`
- Use the 8-section template (see *TCD KB File Format* below)
- Mandatory: populate **§1** (scenario intro + TC coverage map), **§5** (measurable
  pass/fail bar), and a `> **Architecture overview:** See TPF §2` pointer
- Run **lint gate L1–L7** (see below); fix failures before proceeding

**REFRESH mode:**
- Re-fetch live HSD description + TC list
- Update KB sections that are HSD-derived: title, TC coverage map, parent TPF link
- **Preserve** human-authored enrichment content in other sections
- Run lint gate; fix failures before proceeding

### Lint Gate (L1–L7)

| ID | Check | Block? |
|----|-------|--------|
| L1 | Section 1 intro ≤80 words | Warning |
| L2 | No architecture diagrams in §1 (moved to TPF §2) | Block |
| L3 | No numbered test steps / tool command lines in §1–§4 (those → TC) | Block |
| L4 | §5 contains at least one measurable threshold (quantity / register value / %) | Block |
| L5 | §5 bar is not identical to a sibling TCD’s bar (uniqueness check) | Warning |
| L6 | §6 corner cases use 4-column verdict table, not bullet list | Warning |
| L7 | Parent TPF link present in §1 | Warning |

On any **Block** failure: fix the KB file, re-lint, then continue to Step 3.

---

## Step 3 — Generate Preview

```powershell
# From repo root
python tools/html/generate_tcd_preview.py --tcd <TCD_ID> --force
# Output: tcd_description_output/TCD_{id}_{slug}_preview.html
```

The output must have a `<div class="desc-box">` wrapper (push contract). If it
does not, the generator has a bug — do not proceed to Step 4.

---

## Step 4 — ⚠️ Mandatory Review Gate (hard stop)

After generating the preview, **stop and print exactly**:

```
Preview ready at tcd_description_output/TCD_{ID}_{slug}_preview.html
Push to HSD? (yes / no — if no, tell me what to change)
```

**Rules:**
- Do **NOT** call `push_preview.py` or any HSD write tool before receiving an
  explicit “yes” from the user.
- A “yes” from **before the most recent regeneration** does not count. If the
  user requests changes, apply them to the **KB file** (never to the HTML),
  regenerate, and ask again.
- If the user says “no” or requests changes: apply edits → regenerate → return
  to this gate.

---

## Step 5 — Push (only after explicit yes)

```powershell
# Dry-run if content_len changed by >50% vs last known push
python tools/hsd/push_preview.py --dry-run tcd_description_output/TCD_{TCD_ID}_{slug}_preview.html

# Full push
python tools/hsd/push_preview.py tcd_description_output/TCD_{TCD_ID}_{slug}_preview.html
```

Expected output:
```
  file    : tcd_description_output/TCD_{ID}_..._preview.html
  hsd_id  : {ID}  (https://hsdes.intel.com/appstore/article-one/#/{ID})
  subject : test_case_definition
  content : {N} chars
  result  : 200 OK
```

After 200 OK: read back the HSD article and confirm `len(description)` is within
±5% of `content_len` to detect silent truncation.

> **Never use temp `.py` files or inline Python in PowerShell heredocs.**
> `push_preview.py` handles desc-box extraction, Kerberos auth, and subject routing.
> Source: `tools/hsd/push_preview.py`

---

## TCD KB File Format

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

**Content routing (enforced before writing any section):**

| Content type | Belongs in | NOT in TCD |
|-------------|-----------|------------|
| Feature architecture diagrams / boot flows | **TPF §2** | TCD §1 |
| Runtime control flow (numbered HOW steps) | **TC §4 Steps** | TCD §1 |
| Tool command lines (`kayak`, `isst`, script paths) | **TC §3 Automation** | TCD |
| BIOS register execution sequence (step-by-step procedure) | **TC §2/§4** | TCD §4 |
| BIOS register theory (WHAT registers are involved, invariants) | **TCD §4** | TC |
| **Pass/fail criteria bar** | **TCD §5** — TC §5 *references* the TCD bar | Never define independently in TC |
| Feature programming theory (WHAT the feature does operationally) | TCD §4 | TC (exec details) |

See `nwp-tc-description` skill for the full HOW content authoring guide.

### Recommended Section 1 Structure

```markdown
## Section 1: Architecture / Micro-architecture and Functionality

Intro paragraph ≤80 words. WHAT this scenario validates and why it matters. No diagrams, no numbered steps.

> **Architecture overview:** See [TPF {ID} — {Title}]({url}) §2 Design Details
> for boot flow, feature mechanism, and frequency hierarchy.

### NWP-Specific Deltas
- Delta item 1 (scenario-specific constant or NWP difference from GNR/DMR)

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [HSD ID — Title](url) | scenario description | FV / PSS / PV |
```

**Removed from template:** `### Runtime Control Flow` (→ TC §4 Steps), `### Block Decomposition` (→ TPF §2 Design Details), `### Scope Boundary` (sibling TCD enumeration tables are navigation, not WHAT content — the TPF §8 TCD Coverage table already provides this view at the right abstraction level).

### Push to HSD — Extract desc-box only (skip header)

When pushing TCD preview HTML to HSD, extract only the `desc-box` div content.

**WARNING — do NOT use the regex pattern here.** TCD preview HTML has many nested `</div>` tags inside the description body. The non-greedy `.*?` regex stops at the first `</div>` inside the content (an empty match). Always use the **index-based extraction** instead:

```python
html = open('tcd_description_output/TCD_{id}_{slug}_preview.html', encoding='utf-8').read()
marker = '<div class="desc-box">'
start  = html.index(marker) + len(marker)
end    = html.rindex('</div>', 0, html.index('</body>'))
content = html[start:end].strip()
# Then PUT content to HSD
```

The `rindex` finds the **last** `</div>` before `</body>`, which is the desc-box closing tag. This correctly captures all nested section content.

### PowerShell heredoc warning

**Avoid** writing KB content via PowerShell heredoc (`@'...'@`) for lines with `**bold**`.
PowerShell can introduce extra `**` at line boundaries (e.g. `**text****` instead of `**text** `),
causing inverted bold in the rendered HTML. Prefer writing KB files directly via the `create_file`
tool or `replace_string_in_file`.



---

## Step 4a — Section 6 Corner Cases Coverage Review

When the user asks "does this grade today" or "will existing TCs cover this?", perform a
coverage verdict for every corner case in Section 6 before generating/updating the preview.

### Coverage Verdict Table Format

Replace bullet-list corner cases with a structured 4-column table:

```markdown
## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Name** | What can go wrong | ✅ Covered by TC XXXXXXX / ⚠️ Verification criterion only / ❌ Not covered | No action / Add as pass criterion in TC X / New TC needed |
```

### Coverage Verdict Rules

| Verdict | When to use | Action |
|---------|------------|--------|
| ✅ **Covered** | An existing TC explicitly exercises this scenario as a test step or pass criterion | No action |
| ⚠️ **Verification criterion only** | No standalone TC needed — should be an explicit check *within* existing TCs (e.g. dual-read alignment, precondition guard) | Note which TCs to add the check to |
| ❌ **Gap — new TC needed** | Scenario has no coverage path in any existing TC under this TCD | State recommended TC scope; note analogous TC from sibling TCD if one exists |

### Typical Gap Patterns

- **Negative boundary** (max+1, out-of-range knob value): positive-path sweep TCs never test this → gap
- **Post-transition stale state**: TC that starts from a disabled state cannot verify clean removal of prior-enabled state → must start from prior-enabled baseline
- **Cross-register alignment** (sysfs vs MSR vs TPMI): not a standalone TC; add as dual-read pass criterion
- **Infrastructure prerequisites** (driver loaded, tool present): precondition guard, not a TC

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
1. Architecture / Micro-architecture and Functionality — WHAT the scenario validates; NWP deltas; TC coverage map; pointer to TPF §2 for architecture diagrams
2. Interfaces and Protocols — registers/sysfs/MSRs this scenario touches (≤15 rows, scenario-relevant only)
3. Reset, Power, and Clocking — which boot phase scenario begins; relevant state transitions
4. Programming Model — **WHAT registers/interfaces are involved conceptually and the feature’s operational invariants** (e.g. “PCT is configured at BIOS CPL3 via Partition Count knob; OS discovers HP/LP topology via sysfs — validation observes what the OS sees”). NOT test steps, NOT command lines, NOT register write order (those → TC).
5. Operational Behavior — scenario × expected outcome × TC links table
6. Corner Cases & Error Handling — 4-column coverage verdict (see Step 4a)
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

### Stale KB File Handling

The preview generator finds the KB file by glob `*{TCD_ID}*.md`. If an existing KB file
has the **correct ID but wrong title slug** (HSD article was renamed after initial caching):

1. **Verify live title first** — fetch `id,title` from HSD before assuming the cached title is correct
2. **Rename stale file** to remove the ID from its filename (prevents glob collision):
   ```powershell
   Rename-Item 'KB/pm_tcd_kb/.../TCD_{id}_old_slug.md' 'TCD_STALE_old_slug_ref.md'
   ```
3. **Create new file** with correct slug: `TCD_{id}_{correct_slug}.md`
4. Add a comment at the top of the stale file: `<!-- STALE: HSD {id} renamed. See TCD_{id}_{new_slug}.md -->`

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Generic Feature Overview ("Validate X on NWP") | Replace with spec-derived content using HAS/MAS |
| Missing register paths | Read KB/pm_features article or query codesign-ask-specs-and-wikis |
| Updating HSD before preview | Always preview first, wait for confirm |
| PowerShell quote mangling in push script | Write script to temp `.py` file, run it, then delete — never inline double-quoted Python in `@"..."@` |
| Wrong subject in PUT | Use `subject: test_case_definition` for TCD (not `test_case`) |
| Section 4 contains TC test code | Section 4 = feature programming theory (register sequence, BIOS flow, OS discovery). Move test code to TC descriptions, not TCD |
| Architecture diagram in TCD Section 1 | Feature-wide diagrams (boot flow, CLOS mechanism, frequency hierarchy) belong in TPF Section 2 — use `nwp-tpf-description` skill to extract and promote them |
| Test steps / command lines in TCD | Numbered HOW steps and tool commands belong in TC — use `nwp-tc-description` skill to author TC descriptions |
| Pass/fail criteria authored in TC §5 instead of TCD §5 | **The bar lives in TCD.** Move measurable thresholds and acceptance criteria to TCD §5. TC §5 = measurement procedure + link to TCD bar only. Multiple TCs against one TCD will otherwise have contradictory bars. |
| TCD Section 5 has no measurable bar (L5 lint) | TCD §5 must state the acceptance threshold (e.g. “PC6 residency counter ≥ X within Y sec”). A TCD with only scenario → expected-behavior → TC-link rows but no quantitative bar is incomplete — block enrichment. |
| Stale KB filename (ID present, title wrong) | Fetch live HSD title first; rename stale file to `TCD_STALE_*` (removes ID from glob); create new file with correct slug |
| Section 6 as bullet list only | Convert to 4-column coverage table (Corner Case / Description / Current Coverage / Action Required) when assessing gaps |

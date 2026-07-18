---
name: nwp-tc-description
description: >
  Author, enrich, and update NWP PM Test Case (TC) descriptions in HSD.
  Owns the HOW content: exact test steps, tool commands, BIOS register sequences,
  pass/fail criteria, and environment setup. TCD describes WHAT to validate;
  TC describes HOW to validate it.
---

# NWP TC Description Skill

> Repo root: `c:/github/nwp_testplan/`
> Hierarchy: TP → TPF → **TCD** → **TC** → TR
> Phoenix: TC = "HOW to validate". TC inherits WHAT from parent TCD.
> Related: `nwp-tcd-description` (WHAT), `nwp-tpf-description` (Design Details)

---

## Content Routing — What belongs in a TC vs TCD

| Content type | TC (HOW) | TCD (WHAT) | TPF (Design Details) |
|-------------|----------|-----------|---------------------|
| Test step sequence (numbered) | ✅ | ❌ | ❌ |
| Tool command lines (`kayak`, `python`, `isst`) | ✅ | ❌ | ❌ |
| BIOS register sequences used during test | ✅ | ❌ | ❌ |
| Pass/fail criteria with exact values | ✅ | ❌ | ❌ |
| OS API calls / sysfs paths used in assertions | ✅ | ❌ | ❌ |
| Environment setup (BIOS knobs, driver state) | ✅ | ❌ | ❌ |
| Expected output snippets / register dump | ✅ | ❌ | ❌ |
| Scenario WHAT (what is being proven) | ❌ | ✅ | ❌ |
| Feature architecture diagrams / flows | ❌ | ❌ | ✅ |
| NWP-specific constants (freq targets, core count) | ❌ | ✅ (brief) | ✅ (full) |

---

## When to Use

- User asks to write, enrich, or update a TC description
- TC description is generic ("run kayak") with no test steps or pass/fail criteria
- TC inherits a rich TCD and needs the HOW details filled in
- User says `enrich tc <ID>`, `write tc steps <ID>`, `update tc <ID>`

---

## TC Description Structure (5 sections)

Phoenix TC = HOW to validate. Sections map to Phoenix TC fields:

```
1. Validation Scope       ← WHAT this TC specifically validates (≤80 words; inherited from TCD)
2. Preconditions          ← Platform, BIOS knobs, driver state, tool availability
3. Automation             ← Exact command line(s) to run the test
4. Test Steps             ← Numbered sequence: action → expected result per step
5. Pass/Fail Criteria     ← Explicit measurable criteria — REQUIRED, no TCs without this
```

### Section 1: Validation Scope

One short paragraph. What specific scenario does this TC cover?
Should align to one row in the parent TCD's Section 5 Operational Behavior table.

```markdown
Verify [specific scenario] on NWP [platform/environment].
Validates that [observable outcome] when [condition].
Parent TCD: [TCD ID — Title](url) — [which scenario row].
```

### Section 2: Preconditions

| Requirement | Detail |
|-------------|--------|
| Platform | NWP-IMH system / PSS VP (Simics) / HSLE XOS |
| BIOS knobs | `EDKII → Socket Config → ...` = `value` |
| OS / Driver | Ubuntu; `scaling_driver = intel_pstate`; `intel-speed-select` installed |
| Feature state | PCT enabled / disabled; partition_count = N |
| Tool | `kayak` installed; `sst_launcher.py` accessible |
| Starting state | e.g. "start from prior-enabled PCT state" |

### Section 3: Automation

```markdown
**Command line:**
`kayak -p kayak.plugins.sst.plugin tests\contents\powermanagement\sst\sst_launcher.py --test <TEST_NAME>`

**Script / tool:** `sst_launcher.py`
**Test function:** `SST_PCT_MODULE_*`
**Estimated runtime:** ~N minutes
```

For PythonSV-based TCs:
```python
# Automation entry point
python scripts/pm/pss/pct_test.py --scenario <scenario>
```

### Section 4: Test Steps

Numbered sequence. Each step = **one action** + **one expected result**.

```markdown
1. **Set BIOS knob** — PCT Partition Count = N. Expected: knob accepts value; no error in BIOS Setup.
2. **Boot system** — power cycle to Ubuntu. Expected: OS boot completes; `dmesg` shows no SST errors.
3. **Verify intel-speed-select topology** — run `intel-speed-select perf-profile info`. Expected: N HP modules reported with correct APIC IDs.
4. **Read cpufreq caps per core** — for each cpu in all_cpus, read `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq`. Expected: HP cores = ~4.4 GHz ceiling; LP cores = ~2.3 GHz ceiling.
5. **Assert HP > LP** — verify `max(hp_freqs) > max(lp_freqs)`. Expected: assertion passes.
```

**Rules for test steps:**
- Each step must be independently verifiable
- Include the exact register path / sysfs path / command used
- Include the exact expected value or comparison
- Never omit the "Expected:" line — that IS the pass/fail logic

### Section 5: Pass/Fail Criteria

Explicit measurable criteria. Phoenix requires this field for TC completion.

```markdown
**PASS** when ALL of the following are true:
- HP core `cpuinfo_max_freq` ≥ `hp_trl_khz × 0.95` for all HP CPUs
- LP core `cpuinfo_max_freq` ≤ `lp_clip_khz × 1.05` for all LP CPUs
- `intel-speed-select` reports correct HP module count = `partition_count × 2`
- No dmesg errors related to SST or PCT during test

**FAIL** when ANY of the following are true:
- Any HP core `cpuinfo_max_freq` below HP TRL threshold
- Any LP core `cpuinfo_max_freq` above LP clip threshold
- `intel-speed-select` reports wrong HP count or missing modules
- SST-related dmesg errors observed
```

---

## HOW Content Patterns (reference)

### BIOS register sequence in TC (not TCD)

When a TC requires specific BIOS register programming, document it in the **Preconditions** or **Test Steps** — NOT in the TCD Section 4.

```markdown
# In TC Preconditions:
| Req | Detail |
|-----|--------|
| BIOS programming | BIOS CPL3 programs: SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.ratio_0; SST_CP_CONTROL.priority_type = 1 |

# In TC Test Steps:
1. Confirm BIOS has programmed SST_CLOS_CONFIG[0].max:
   - Run: `sv.socket0.nio0.tpmi.sst_clos_config_0.read()`
   - Expected: value = SST_TF_INFO_2.ratio_0 (~0x2C for 4.4 GHz on NWP)
```

### OS API / sysfs assertions in TC (not TCD)

```markdown
# In TC Test Steps:
3. Read per-core frequency caps:
   - Run: `for c in range(96): open(f'/sys/bus/cpu/devices/cpu{c}/cpufreq/cpuinfo_max_freq').read()`
   - Expected: cores 0,24,48,72 (HP) report ≥4,400,000; all others report ≤2,300,000
```

### PythonSV assertions in TC (not TCD)

```markdown
4. Read TPMI CLOS assignment per core:
   - Run: `[nio.tpmi.sst_clos_assoc.read_field(f'clos_{i}') for i in range(96)]`
   - Expected: HP cores → 0 (CLOS[0]); LP cores → 3 (CLOS[3])
```

---

## Push to HSD

TCs use `subject: test_case`. Same index-based extraction as TCD:

```python
html = open('tc_description_output/TC_{id}_{slug}_preview.html', encoding='utf-8').read()
marker = '<div class="desc-box">'
start  = html.index(marker) + len(marker)
end    = html.rindex('</div>', 0, html.index('</body>'))
content = html[start:end].strip()

r = s.put(f'https://hsdes-api.intel.com/rest/article/{TC_ID}',
    json={'tenant': 'server', 'subject': 'test_case',
          'fieldValues': [{'description': content}, {'send_mail': 'false'}]},
    timeout=60)
```

> **Subject**: `test_case` (not `test_case_definition` — that is TCD)

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Test steps in TCD Section 4 | Move numbered test steps to TC; TCD Section 4 = feature programming theory only |
| Pass/fail criteria missing | Always required in TC Section 5 — block TC if absent |
| `kayak` command in TCD | Command lines belong in TC Section 3, not TCD |
| OS API calls (`cpuinfo_max_freq`, `isst`) in TCD | Move to TC test steps; TCD references the observable outcome only |
| BIOS register sequence in TCD Section 4 | Move specific test-time register reads/writes to TC preconditions or steps; TCD Section 4 = what registers are involved conceptually |
| Missing "Expected:" in test step | Every step must have an expected result — it IS the pass/fail logic |

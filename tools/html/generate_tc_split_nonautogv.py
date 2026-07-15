"""
Generate TC split review HTML: CBB CCF NonAutoGV Fast GV → TC1 (FLL POR) + TC2 (PLL Crawling).
Output: tcd_description_output/TC_Split_Review_NonAutoGV_FastGV.html
"""

import pathlib

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>TC Split Review — CBB CCF NonAutoGV Fast GV</title>
<style>
:root{--primary:#1e3a5f;--accent:#2563eb;--green:#16a34a;--orange:#ea580c;--red:#dc2626;--bg:#f8fafc;--card:#fff;--border:#e2e8f0;--text:#1e293b;--muted:#64748b;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.6;}
.header{background:linear-gradient(135deg,#0f2744,#1e4d8c 60%,#2563eb);color:white;padding:32px 48px 24px;}
.header h1{font-size:1.7rem;font-weight:800;margin-bottom:6px;}
.header .sub{font-size:0.9rem;opacity:.85;margin-bottom:18px;}
.header-meta{display:flex;gap:32px;flex-wrap:wrap;}
.meta{display:flex;flex-direction:column;}
.meta-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.06em;opacity:.65;}
.meta-value{font-size:.95rem;font-weight:700;}
.rationale{background:white;border-left:4px solid var(--accent);margin:24px 48px;padding:18px 24px;border-radius:0 8px 8px 0;box-shadow:0 1px 4px rgba(0,0,0,.07);}
.rationale h2{font-size:1rem;font-weight:700;color:var(--primary);margin-bottom:10px;}
.rationale ul{margin-left:18px;font-size:.88rem;}
.rationale li{margin-bottom:4px;}
.split-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:0 48px 40px;}
.tc-card{background:var(--card);border-radius:12px;border:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.06);overflow:hidden;}
.tc-header{padding:18px 22px 14px;border-bottom:1px solid var(--border);}
.tc-type-badge{display:inline-block;font-size:.7rem;font-weight:800;border-radius:4px;padding:2px 10px;margin-bottom:8px;}
.existing .tc-type-badge{background:#dcfce7;color:#16a34a;border:1px solid #16a34a;}
.new-tc .tc-type-badge{background:#dbeafe;color:#1d4ed8;border:1px solid #1d4ed8;}
.tc-id{font-size:.78rem;font-weight:700;color:var(--muted);margin-bottom:4px;}
.tc-title{font-size:1.05rem;font-weight:700;color:var(--primary);}
.tc-intent{font-size:.82rem;color:var(--muted);margin-top:6px;padding-top:6px;border-top:1px solid var(--border);}
.tc-body{padding:18px 22px;}
.section{margin-bottom:18px;}
.section-title{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--primary);border-left:3px solid var(--accent);padding-left:8px;margin-bottom:10px;}
table.tc-table{width:100%;border-collapse:collapse;font-size:.8rem;}
table.tc-table th{background:#f1f5f9;color:var(--muted);padding:7px 10px;text-align:left;font-size:.7rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--border);}
table.tc-table td{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top;}
.step-num{font-weight:700;color:var(--accent);white-space:nowrap;}
.pass-cell{font-size:.78rem;color:#166534;background:#f0fdf4;border-left:3px solid #16a34a;padding-left:8px;}
.fail-cell{font-size:.78rem;color:#991b1b;background:#fef2f2;border-left:3px solid var(--red);padding-left:8px;}
.pf-block{background:#f8fafc;border-radius:6px;padding:10px 14px;font-size:.82rem;}
.pf-pass{color:#166534;margin-bottom:6px;}<br>
.pf-fail{color:#991b1b;}
.pre-block{background:#1e293b;color:#e2e8f0;border-radius:8px;padding:14px 16px;font-family:'Courier New',monospace;font-size:.78rem;overflow-x:auto;margin-bottom:0;}
.pre-block .comment{color:#64748b;}
.pre-block .kw{color:#7dd3fc;}
.pre-block .fn{color:#86efac;}
.pre-block .str{color:#fde68a;}
.pre-block .op{color:#f472b6;}
.script-badge{display:inline-block;background:#1e293b;color:#86efac;border-radius:4px;padding:2px 8px;font-family:monospace;font-size:.75rem;margin-top:4px;}
.change-badge{display:inline-block;font-size:.68rem;font-weight:700;border-radius:4px;padding:1px 7px;margin-left:6px;}
.badge-new{background:#dbeafe;color:#1d4ed8;}
.badge-updated{background:#fef9c3;color:#92400e;}
.badge-unchanged{background:#f1f5f9;color:var(--muted);}
.reg-chip{display:inline-block;font-size:.7rem;background:#f1f5f9;border:1px solid #d1d5db;border-radius:3px;padding:1px 5px;font-family:monospace;margin:1px;}
.prereq-table td{font-size:.8rem;padding:5px 10px;border-bottom:1px solid var(--border);}
.prereq-table th{font-size:.7rem;padding:5px 10px;background:#f1f5f9;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--border);}
.scope-delta{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;font-size:.82rem;color:#78350f;margin-top:12px;}
.scope-delta h4{font-weight:700;margin-bottom:6px;}
.scope-delta ul{margin-left:16px;}
.footer{background:var(--primary);color:white;text-align:center;padding:14px;font-size:.78rem;opacity:.8;margin-top:0;}
@media(max-width:900px){.split-grid{grid-template-columns:1fr;padding:0 16px 32px;}.header{padding:24px 20px;}.rationale{margin:16px;}}
</style>
</head>
<body>

<div class="header">
  <h1>TC Split Review — CBB CCF NonAutoGV Fast GV</h1>
  <div class="sub">Splitting HSD 22022422878 into two separate TCs per HAS POR vs Survivability scope</div>
  <div class="header-meta">
    <div class="meta"><span class="meta-label">Source TC</span><span class="meta-value">22022422878 — CBB CCF NonAutoGV Mode - Fast GV</span></div>
    <div class="meta"><span class="meta-label">Parent TCD</span><span class="meta-value">22022421183 — CBB CCF NonAutoGV Mode - Drainless / Fast GV</span></div>
    <div class="meta"><span class="meta-label">Prepared</span><span class="meta-value">2026-07-15</span></div>
    <div class="meta"><span class="meta-label">Script</span><span class="meta-value">pm/Active_PM/CCF_GV/pmx_ccf_cbo.py</span></div>
  </div>
</div>

<div class="rationale">
  <h2>Why split?</h2>
  <ul>
    <li><strong>Different spec scope:</strong> POR config is Fast GV with PLLs in their default state (<code>pll_mode=0</code>). PLL crawling (<code>pll_mode=1</code> override + fuse-driven crawl params) is a <em>survivability</em> path, not the mainline.</li>
    <li><strong>Different failure modes:</strong> TC1 failure = AutoGV wrongly enabled or CCF_WP not honoured. TC2 failure = pll_mode override not accepted or frequency doesn't crawl within <code>freq_crawl_delta_f</code> steps.</li>
    <li><strong>Script already separates them:</strong> <code>cbb_ccf_fast_gv_default_test()</code> vs <code>cbb_ccf_fast_gv_pll_crawling_test()</code> are already distinct functions — they just share one CLI flag today.</li>
    <li><strong>Current PLL crawling test is a stub:</strong> It only writes/reads <code>pll_mode</code> — no actual GV sweep under crawl constraints. TC2 fills that gap with a real PEGA-driven sweep.</li>
    <li><strong>Cleaner regression tagging:</strong> POR Fast GV runs on every boot regression; PLL crawling runs on survivability pass only.</li>
  </ul>
</div>

<div class="split-grid">

<!-- ═══════════════════════════════════════ TC1 ═══════════════════════════════════════ -->
<div class="tc-card existing">
  <div class="tc-header">
    <div class="tc-type-badge">EXISTING — UPDATED TITLE</div>
    <div class="tc-id">HSD <a href="https://hsdes.intel.com/appstore/article-one/#/22022422878" target="_blank">22022422878</a> &nbsp;<span class="change-badge badge-updated">Title + Description Updated</span></div>
    <div class="tc-title">CBB CCF NonAutoGV Mode — Fast GV Default (FLL Mode / POR)</div>
    <div class="tc-intent">Verify that CBB CCF powers up and operates in NonAutoGV mode using the default PLL configuration (<code>pll_mode=0</code>). Confirm AutoGV is not active, CCF_WP accepts PEGA workpoints, UFS_STATUS tracks the injected ratio, and the mode persists across C-state cycles.</div>
  </div>
  <div class="tc-body">

    <div class="section">
      <div class="section-title">Pre-Conditions</div>
      <table class="tc-table prereq-table">
        <thead><tr><th>Condition</th><th>Check</th></tr></thead>
        <tbody>
          <tr><td>OS booted to CPL4</td><td>BIOS complete; PCode + CCF PMA initialized</td></tr>
          <tr><td>CCF in NonAutoGV (PLL) mode</td><td><code>ringepll/ringwpll.fusecr_ovrd_0.pll_mode == 0</code> on all CBBs</td></tr>
          <tr><td>PEGA imported</td><td><code>import pm.pmutils.pega as pega</code></td></tr>
          <tr><td>CCF_WP readable</td><td><code>cbb.base.ccf_pma.ccf_pmc_regs.ccf_wp[0]</code> accessible</td></tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Test Steps</div>
      <table class="tc-table">
        <thead><tr><th style="width:32px">#</th><th>Action</th><th>Expected (PASS)</th></tr></thead>
        <tbody>
          <tr><td class="step-num">1</td><td>Read <code>ringepll_top.fusecr_ovrd_0.pll_mode</code> and <code>ringwpll_top.fusecr_ovrd_0.pll_mode</code> per CBB</td><td>Both == 0 (PLL mode) on all CBBs — AutoGV not active</td></tr>
          <tr><td class="step-num">2</td><td>Verify <code>pll_mode_ovrden == 0</code> — no override active at boot</td><td>Override not asserted = hardware default state confirmed</td></tr>
          <tr><td class="step-num">3</td><td>Inject CCF_WP via PEGA: <code>ccf_pegaPstate(sktNum, cbbN, clrgv=target_ratio, chkstr='ccf_wp,ufs_status')</code> sweeping Pm→P0</td><td><code>ccf_wp[0].target_max_ratio</code> matches injected value; <code>ufs_status.current_ratio</code> tracks workpoint</td></tr>
          <tr><td class="step-num">4</td><td>Read <code>ccf_wp_status.ratio</code> after each injection</td><td>Matches injected <code>clrgv</code> — PCode interpretation correct</td></tr>
          <tr><td class="step-num">5</td><td>Cycle core C-state: inject <code>c1e</code> via PEGA, release to C0, re-read <code>pll_mode</code></td><td><code>pll_mode</code> still 0 after C-state — NonAutoGV persists</td></tr>
          <tr><td class="step-num">6</td><td>Release PEGA; verify <code>ufs_status.current_ratio</code> returns to fused P0</td><td>Ratio returns to fused maximum — no stuck workpoint</td></tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Pass / Fail</div>
      <div class="pf-block">
        <div class="pf-pass">✓ PASS: All CBBs show <code>pll_mode==0</code> at boot; <code>ccf_wp</code> + <code>ufs_status.current_ratio</code> track PEGA injected ratios; mode unchanged after C-state.</div>
        <div class="pf-fail">✗ FAIL: Any CBB with <code>pll_mode!=0</code> at boot; CCF_WP not reflecting PEGA injection; ratio stuck after PEGA release.</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Script</div>
      <div class="script-badge">pmx_ccf_cbo.py --test_ccf_fast_gv</div>
      <div style="margin-top:8px;font-size:.78rem;color:var(--muted)">Calls: <code>cbb_ccf_fast_gv_default_test()</code> — no changes needed to existing function</div>
    </div>

    <div class="section">
      <div class="section-title">Key Registers</div>
      <code class="reg-chip">ringepll_top.fusecr_ovrd_0.pll_mode</code>
      <code class="reg-chip">ringwpll_top.fusecr_ovrd_0.pll_mode</code>
      <code class="reg-chip">ringepll_top.fusecr_ovrd_0.pll_mode_ovrden</code>
      <code class="reg-chip">ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio</code>
      <code class="reg-chip">punit_pmsb.pmsb_pcu.ccf_wp_status.ratio</code>
      <code class="reg-chip">tpmi.ufs_status.current_ratio</code>
    </div>

    <div class="scope-delta">
      <h4>Changes from original TC</h4>
      <ul>
        <li>Title updated: <em>"Fast GV Default (FLL Mode / POR)"</em> — clarifies this is the POR path</li>
        <li>Step 2 added: explicit check that <code>pll_mode_ovrden==0</code> (no override at boot)</li>
        <li>Step 3 updated: full Pm→P0 sweep with <code>chkstr='ccf_wp,ufs_status'</code></li>
        <li>Step 5 strengthened: C-state persistence explicitly checks <code>pll_mode</code> after C1e cycle</li>
        <li>PLL crawling steps <strong>removed</strong> → moved to TC2</li>
      </ul>
    </div>

  </div>
</div>

<!-- ═══════════════════════════════════════ TC2 ═══════════════════════════════════════ -->
<div class="tc-card new-tc">
  <div class="tc-header">
    <div class="tc-type-badge">NEW TC — CREATE IN HSD</div>
    <div class="tc-id">Parent TCD: <a href="https://hsdes.intel.com/appstore/article-one/#/22022421183" target="_blank">22022421183</a> &nbsp;<span class="change-badge badge-new">New</span></div>
    <div class="tc-title">CBB CCF NonAutoGV Mode — Fast GV with PLL Crawling Override</div>
    <div class="tc-intent">Verify that CBB CCF ring frequency transitions correctly when PLL crawl mode is forced via <code>pll_mode_ovrden=1 + pll_mode=1</code>. Validate that GV sweeps complete within frequency crawl constraints (<code>freq_crawl_delta_f</code>) and that the system restores to default PLL mode cleanly after the test.</div>
  </div>
  <div class="tc-body">

    <div class="section">
      <div class="section-title">Pre-Conditions</div>
      <table class="tc-table prereq-table">
        <thead><tr><th>Condition</th><th>Check</th></tr></thead>
        <tbody>
          <tr><td>OS booted to CPL4</td><td>Same as TC1</td></tr>
          <tr><td>CCF in default PLL mode</td><td><code>pll_mode==0</code> on all CBBs before test starts</td></tr>
          <tr><td>PEGA imported + released</td><td><code>pega.release(1)</code> before injection</td></tr>
          <tr><td>Fused crawl params readable</td><td><code>freq_crawl_disable</code>, <code>freq_crawl_delta_f</code>, <code>freq_crawl_delta_t</code> accessible</td></tr>
          <tr><td>UFS fused min/max known</td><td><code>tpmi.sst_pp_info_11.pm_fabric_ratio</code> and <code>p0_fabric_ratio</code></td></tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Test Steps</div>
      <table class="tc-table">
        <thead><tr><th style="width:32px">#</th><th>Action</th><th>Expected (PASS)</th></tr></thead>
        <tbody>
          <tr><td class="step-num">1</td><td>Read and save current <code>pll_mode</code> and <code>pll_mode_ovrden</code> per CBB (baseline)</td><td>Both == 0 (default PLL mode, no override)</td></tr>
          <tr><td class="step-num">2</td><td>Read fused crawl params: <code>freq_crawl_disable</code>, <code>freq_crawl_delta_f</code>, <code>freq_crawl_delta_t</code> per CBB</td><td>Values readable; <code>freq_crawl_disable==0</code> (crawl enabled by fuse)</td></tr>
          <tr><td class="step-num">3</td><td>Assert PLL crawl override: write <code>pll_mode_ovrden=1</code> then <code>pll_mode=1</code> on Ring East and West per CBB</td><td>Readback: <code>pll_mode_ovrden==1</code> and <code>pll_mode==1</code> on both rings</td></tr>
          <tr><td class="step-num">4</td><td>Perform PEGA GV sweep Pm→P0 in steps of 1 ratio unit: <code>ccf_pegaPstate(clrgv=r, chkstr='ufs_status')</code></td><td><code>ufs_status.current_ratio</code> follows each requested step; no step exceeds <code>freq_crawl_delta_f</code></td></tr>
          <tr><td class="step-num">5</td><td>Perform reverse sweep P0→Pm and verify same crawl constraint holds</td><td>Frequency decrements within <code>freq_crawl_delta_f</code> per step; no large jumps</td></tr>
          <tr><td class="step-num">6</td><td>Release PEGA; restore <code>pll_mode_ovrden=0</code> + <code>pll_mode=0</code> per CBB</td><td>Readback confirms <code>pll_mode==0</code> and <code>pll_mode_ovrden==0</code> — default restored</td></tr>
          <tr><td class="step-num">7</td><td>Inject PEGA GV at P0 with no override active; verify <code>ufs_status.current_ratio</code></td><td>Ratio reaches P0 directly (no crawl constraint) — confirms PLL mode is default again</td></tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Pass / Fail</div>
      <div class="pf-block">
        <div class="pf-pass">✓ PASS: <code>pll_mode_ovrden=1</code> accepted and reads back correctly; GV sweep completes with each step ≤ <code>freq_crawl_delta_f</code>; no stuck frequency; PLL mode restored after test; post-restore GV sweep hits P0 directly.</div>
        <div class="pf-fail">✗ FAIL: Override not accepted (<code>pll_mode_ovrden</code> readback mismatch); frequency step exceeds <code>freq_crawl_delta_f</code>; stuck ratio after PEGA release; restore to <code>pll_mode=0</code> fails; post-restore sweep does not reach P0.</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Script — New CLI Flag</div>
      <div class="script-badge">pmx_ccf_cbo.py --test_ccf_fast_gv_pll_crawling</div>
      <div style="margin-top:8px;font-size:.78rem;color:var(--muted)">
        Calls: <code>cbb_ccf_fast_gv_pll_crawling_test()</code> — <strong>enhanced function</strong> (see below)<br>
        Separate from <code>--test_ccf_fast_gv</code> — can be run independently
      </div>
      <div style="margin-top:10px;">
        <div class="pre-block">
<span class="comment"># Enhanced cbb_ccf_fast_gv_pll_crawling_test() — ccf_utils.py</span>
<span class="kw">def</span> <span class="fn">cbb_ccf_fast_gv_pll_crawling_test</span>(sktNum, dieName, Log=_log, verbose=None):
    <span class="comment"># Step 1-2: save state + read crawl fuses</span>
    orig_mode = dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode
    freq_crawl_delta_f = dieObj.base.ringepll_top.fusecr_ovrd_0.freq_crawl_delta_f
    <span class="comment"># Step 3: assert crawl override</span>
    dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden.write(1)
    dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode.write(1)   <span class="comment"># 1 = FLL/crawl</span>
    dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode_ovrden.write(1)
    dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode.write(1)
    <span class="comment"># Step 4-5: PEGA GV sweep Pm→P0→Pm with crawl validation</span>
    r_min = dieObj.base.tpmi.sst_pp_info_11.pm_fabric_ratio
    r_max = dieObj.base.tpmi.sst_pp_info_11.p0_fabric_ratio
    <span class="kw">for</span> r <span class="kw">in</span> [*range(r_min, r_max+1), *range(r_max, r_min-1, -1)]:
        prev = dieObj.base.tpmi.ufs_status.current_ratio
        ccf_pegaPstate(sktNum, dieName, clrgv=r, chkstr=<span class="str">'ufs_status'</span>)
        act = dieObj.base.tpmi.ufs_status.current_ratio
        <span class="kw">if</span> abs(act - prev) > freq_crawl_delta_f:
            Log.error(<span class="str">f"ERR: step {hex(prev)}->{hex(act)} > delta_f {freq_crawl_delta_f}"</span>)
            chkr += 1
    <span class="comment"># Step 6: restore default PLL mode</span>
    dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden.write(0)
    dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode.write(0)
    dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode_ovrden.write(0)
    dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode.write(0)
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Key Registers</div>
      <code class="reg-chip">ringepll_top.fusecr_ovrd_0.pll_mode_ovrden</code>
      <code class="reg-chip">ringepll_top.fusecr_ovrd_0.pll_mode</code>
      <code class="reg-chip">ringwpll_top.fusecr_ovrd_0.pll_mode_ovrden</code>
      <code class="reg-chip">ringwpll_top.fusecr_ovrd_0.pll_mode</code>
      <code class="reg-chip">fusecr_ovrd_0.freq_crawl_disable</code>
      <code class="reg-chip">fusecr_ovrd_0.freq_crawl_delta_f</code>
      <code class="reg-chip">fusecr_ovrd_0.freq_crawl_delta_t</code>
      <code class="reg-chip">tpmi.ufs_status.current_ratio</code>
    </div>

    <div class="scope-delta" style="background:#eff6ff;border-color:#bfdbfe;color:#1e40af;">
      <h4>What's new vs existing PLL crawling stub</h4>
      <ul>
        <li><strong>Override enable added:</strong> <code>pll_mode_ovrden=1</code> is now set before <code>pll_mode=1</code></li>
        <li><strong>Fuse params read:</strong> <code>freq_crawl_delta_f</code>, <code>freq_crawl_delta_t</code> verified accessible</li>
        <li><strong>Real GV sweep:</strong> PEGA-driven Pm→P0→Pm with per-step crawl constraint check</li>
        <li><strong>Step-size validation:</strong> each ratio transition ≤ <code>freq_crawl_delta_f</code></li>
        <li><strong>Clean restore + post-restore verification:</strong> step 6+7 confirm default mode recovered</li>
      </ul>
    </div>

  </div>
</div>

</div><!-- split-grid -->

<div class="footer">
  Generated 2026-07-15 &nbsp;|&nbsp; NWP PM Test Plan Repo &nbsp;|&nbsp; Parent TCD: 22022421183 — CBB CCF NonAutoGV Mode - Drainless / Fast GV
</div>

</body>
</html>"""

out = pathlib.Path("tcd_description_output/TC_Split_Review_NonAutoGV_FastGV.html")
out.write_text(HTML, encoding="utf-8")
print(f"Written: {out} ({out.stat().st_size:,} bytes)")

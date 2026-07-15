"""Push TCD/TC descriptions to HSD. Supports --tcd and --tc2 modes."""
import sys
import requests
from requests_kerberos import HTTPKerberosAuth, OPTIONAL

BASE = 'https://hsdes-api.intel.com/rest/article'
sess = requests.Session()
sess.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
sess.verify = False
sess.headers.update({'Content-Type': 'application/json'})

# Determine mode
mode = sys.argv[1] if len(sys.argv) > 1 else '--tc2'

if mode == '--tcd':
    # Push TCD 22022421183 full description
    import pathlib
    html_path = pathlib.Path('tcd_description_output/TCD_22022421183_cbb_ccf_nonautogv_mode_preview.html')
    if not html_path.exists():
        print('ERROR: HTML not found. Run: python tools/html/generate_tcd_preview.py --tcd 22022421183 --force')
        sys.exit(1)
    html = html_path.read_text(encoding='utf-8')
    r = sess.put(
        f'{BASE}/22022421183',
        json=dict(subject='test_case_definition', tenant='server',
                  fieldValues=[dict(description=html), dict(send_mail='false')]),
        timeout=30
    )
    print(f'TCD 22022421183 push: {r.status_code} ({len(html)} chars)')
    sys.exit(0)

NEW_ID = '16031123820'

desc = (
    "<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;line-height:1.6;color:#1e293b;max-width:900px'>"
    "<h2 style='color:#1e3a5f;border-bottom:2px solid #2563eb;padding-bottom:6px'>CBB CCF NonAutoGV Mode &mdash; Fast GV with PLL Crawling Override</h2>"
    "<p><strong>Intent:</strong> Verify that CBB CCF ring frequency GV transitions work correctly when PLL crawl mode is forced via <code>pll_mode_ovrden=1 + pll_mode=1</code>. "
    "This is a <strong>survivability / alternate clocking-path test</strong> &mdash; not the POR path. Validates that GV sweeps complete within fuse-defined crawl constraints "
    "(<code>freq_crawl_delta_f</code>), and that the system restores to default PLL mode cleanly after the override. "
    "Sibling to POR Fast GV TC <a href='https://hsdes.intel.com/appstore/article-one/#/22022422878'>22022422878</a>.</p>"

    "<h3 style='color:#1e3a5f;margin-top:14px'>Pre-Conditions</h3>"
    "<table style='width:100%;border-collapse:collapse;font-size:13px'>"
    "<tr style='background:#f1f5f9'><th style='padding:7px 10px;border-bottom:2px solid #e2e8f0'>Pre-Condition</th><th style='padding:7px 10px;border-bottom:2px solid #e2e8f0'>Check</th></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>OS booted to CPL4</td><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>BIOS complete; PCode + CCF PMA initialized</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>CCF in default PLL mode</td><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'><code>pll_mode==0</code> and <code>pll_mode_ovrden==0</code> on all CBBs before test</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>PEGA imported</td><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'><code>pega.release(1)</code> before sweep</td></tr>"
    "<tr><td style='padding:6px 10px'>Fused crawl params readable</td><td style='padding:6px 10px'><code>freq_crawl_disable</code>, <code>freq_crawl_delta_f</code>, <code>freq_crawl_delta_t</code> via <code>ringepll_top.fusecr_ovrd_0</code></td></tr>"
    "</table>"

    "<h3 style='color:#1e3a5f;margin-top:14px'>Test Steps</h3>"
    "<table style='width:100%;border-collapse:collapse;font-size:13px'>"
    "<tr style='background:#f1f5f9'><th style='padding:7px 10px;border-bottom:2px solid #e2e8f0;width:30px'>#</th>"
    "<th style='padding:7px 10px;border-bottom:2px solid #e2e8f0'>Action</th>"
    "<th style='padding:7px 10px;border-bottom:2px solid #e2e8f0'>Expected (PASS)</th></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>1</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Save baseline <code>pll_mode</code> and <code>pll_mode_ovrden</code> per CBB</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Both == 0 (default, no override)</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>2</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Read fused crawl params: <code>freq_crawl_disable</code>, <code>freq_crawl_delta_f</code>, <code>freq_crawl_delta_t</code></td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Values readable; <code>freq_crawl_disable==0</code></td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>3</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Assert crawl override: write <code>pll_mode_ovrden=1</code> then <code>pll_mode=1</code> on Ring E and W per CBB. Verify readback.</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Readback: <code>pll_mode_ovrden==1</code> and <code>pll_mode==1</code> on both rings of all CBBs</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>4</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>PEGA GV sweep Pm&rarr;P0 in 1-ratio-unit steps: <code>ccf_pegaPstate(clrgv=r, chkstr='ufs_status')</code></td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Each step &le; <code>freq_crawl_delta_f</code>; <code>ufs_status.current_ratio</code> tracks each ratio</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>5</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Reverse sweep P0&rarr;Pm with same crawl constraint check</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Each down-step &le; <code>freq_crawl_delta_f</code>; no large jumps</td></tr>"
    "<tr><td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563eb'>6</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Release PEGA; restore <code>pll_mode=0</code> then <code>pll_mode_ovrden=0</code> on all CBBs. Verify readback.</td>"
    "<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0'>Readback confirms <code>pll_mode==0</code> and <code>pll_mode_ovrden==0</code> &mdash; default restored</td></tr>"
    "<tr><td style='padding:6px 10px;font-weight:700;color:#2563eb'>7</td>"
    "<td style='padding:6px 10px'>Post-restore: inject PEGA P0; verify <code>ufs_status.current_ratio</code> reaches P0 directly</td>"
    "<td style='padding:6px 10px'>Ratio at P0 without crawl delay &mdash; confirms default PLL mode active</td></tr>"
    "</table>"

    "<div style='margin-top:14px;padding:12px;background:#f0fdf4;border-left:4px solid #16a34a;border-radius:0 6px 6px 0'>"
    "<strong>PASS:</strong> <code>pll_mode_ovrden=1</code> accepted; each GV step &le; <code>freq_crawl_delta_f</code>; no stuck frequency; "
    "<code>pll_mode==0</code> and <code>pll_mode_ovrden==0</code> after restore; post-restore P0 reached directly."
    "</div>"
    "<div style='margin-top:8px;padding:12px;background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 6px 6px 0'>"
    "<strong>FAIL:</strong> Override not accepted; step &gt; <code>freq_crawl_delta_f</code>; stuck ratio after PEGA release; restore to <code>pll_mode=0</code> fails; post-restore sweep crawls instead of stepping directly."
    "</div>"
    "<p style='margin-top:12px;font-size:12px;color:#64748b'>"
    "<strong>Script:</strong> <code>pmx_ccf_cbo.py --test_ccf_fast_gv_pll_crawling</code> "
    "&nbsp;&bull;&nbsp; <strong>Function:</strong> <code>cbb_ccf_fast_gv_pll_crawling_test()</code> (enhanced: adds pll_mode_ovrden, real GV sweep, crawl constraint check)"
    "</p>"
    "<p style='margin-top:4px;font-size:12px;color:#64748b'>"
    "<strong>Scope:</strong> Survivability / alternate clocking path. Run on survivability regression pass. "
    "POR Fast GV test is TC <a href='https://hsdes.intel.com/appstore/article-one/#/22022422878'>22022422878</a>."
    "</p>"
    "</div>"
)

r = sess.put(
    f'{BASE}/{NEW_ID}',
    json=dict(subject='test_case', tenant='server',
              fieldValues=[dict(description=desc), dict(send_mail='false')]),
    timeout=30
)
print('TC2 description push:', r.status_code)
print('HSD link: https://hsdes.intel.com/appstore/article-one/#/' + NEW_ID)

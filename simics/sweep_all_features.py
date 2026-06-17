"""
sweep_all_features.py — Sweep all PM feature registers from Active_PM scripts.
Runs against live NWP Simics via telnet-frontend tunnel on localhost:4444.
Output: JSON results file consumed by generate_report.py to produce HTML.

Usage:
  python sweep_all_features.py                    # saves as sweep_results.json/html
  python sweep_all_features.py --output fmod_svos # saves as fmod_svos.json/html
"""
import socket, time, re, json, datetime, sys, os

# Output filename stem (no extension)
stem = "sweep_results"
if "--output" in sys.argv:
    stem = sys.argv[sys.argv.index("--output") + 1]

OUT_JSON = os.path.join(os.path.dirname(__file__), stem + ".json")
RESULTS = {"timestamp": datetime.datetime.now().isoformat(), "stem": stem, "features": {}}

CBB0_TPMI   = "sv.socket0.cbb0.base.tpmi"
CBB1_TPMI   = "sv.socket0.cbb1.base.tpmi"
CBB0_PMSB   = "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu"
CBB1_PMSB   = "sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu"
IMH_PMSB    = "sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb"
IMH_FSMS    = "sv.socket0.imh0.punit.ptpcfsms.ptpcfsms"
IMH_IOREGS  = "sv.socket0.imh0.punit.ptpcioregs.ptpcioregs"
CBB0_GPSB   = "sv.socket0.cbb0.compute0.getbypath('pma0').gpsb"


def simics_cmd(s, cmd, wait=3):
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    s.settimeout(1)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            out += chunk
    except Exception:
        pass
    s.settimeout(None)
    txt = out.decode(errors="replace").replace("\r\n", "\n")
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    return txt.strip()


def read_reg(s, label, cmd, wait=3):
    """Read a register and return (label, path, value, status)."""
    r = simics_cmd(s, cmd, wait)
    # strip echo line (first line = command echo)
    lines = [l for l in r.splitlines() if l and not l.startswith(cmd[:20]) and l != "running>"]
    value = "\n".join(lines).strip()
    status = "error" if ("Error" in value or "Traceback" in value or "AttributeError" in value) else "ok"
    path = cmd.replace("@", "").replace(".read()", "").replace(".write(", "=").strip()
    print(f"  {'OK' if status=='ok' else 'ER'} {label}: {value[:80]}")
    return {"label": label, "path": path, "value": value, "status": status}


def sweep_feature(s, name, regs):
    """Sweep a list of (label, cmd) pairs and store results under feature name."""
    print(f"\n{'='*60}\n  {name}\n{'='*60}")
    RESULTS["features"][name] = [read_reg(s, label, cmd) for label, cmd in regs]


s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

# ═══════════════════════════════════════════════════════════════
# PSTATE STACK
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "Pstate_Stack", [
    ("ACP_PERF_LIMIT CBB0 (all FIDs)",              f"@{CBB0_PMSB}.acp_perf_limit.read()"),
    ("ACP_PERF_LIMIT CBB1 (all FIDs)",              f"@{CBB1_PMSB}.acp_perf_limit.read()"),
    ("ACP_PERF_LIMIT IMH0",                          f"@{IMH_PMSB}.acp_perf_limit.read()"),
    ("CORE_ELECTRICAL_REQ IMH0",                     f"@{IMH_PMSB}.core_electrical_req.read()"),
    ("CORE_PM_EVENT IMH0",                           f"@{IMH_PMSB}.core_pm_event.read()"),
    ("UNCORE_VIRTUAL_SIG IMH0",                      f"@{IMH_PMSB}.uncore_virtual_sig.read()"),
    ("PLATFORM_INFO IMH0 (max/min non-turbo ratio)", f"@{IMH_IOREGS}.platform_info.read()"),
    ("ENERGY_PERF_BIAS_CONFIG IMH0 (EPB)",           f"@{IMH_IOREGS}.energy_perf_bias_config.read()"),
    ("SST_PP_INFO_11 IMH0 (P0/P1/Pm ratios)",        f"@{IMH_FSMS}.sst_pp_info_11.read()"),
    ("SST_PP_INFO_4 IMH0 (TRL ratio_0)",             f"@{IMH_FSMS}.sst_pp_info_4.read()"),
    ("OPC_HWP_CAPABILITY CBB0",                     f"@{CBB0_TPMI}.opc_hwp_capability.read()"),
    ("OPC_HWP_CONTROLS CBB0",                       f"@{CBB0_TPMI}.opc_hwp_controls.read()"),
    ("OPC_HWP_CAPABILITY CBB1",                     f"@{CBB1_TPMI}.opc_hwp_capability.read()"),
    ("OPC_HWP_CONTROLS CBB1",                       f"@{CBB1_TPMI}.opc_hwp_controls.read()"),
    ("UFS_STATUS CBB0",                              f"@{CBB0_TPMI}.ufs_status.read()"),
    ("UFS_STATUS CBB1",                              f"@{CBB1_TPMI}.ufs_status.read()"),
    ("SST_PP_INFO_11 CBB0 (P0/P1/Pm ratios)",       f"@{CBB0_TPMI}.sst_pp_info_11.read()"),
    ("SST_PP_INFO_4 CBB0 (TRL ratio_0)",             f"@{CBB0_TPMI}.sst_pp_info_4.read()"),
    ("SST_PP_INFO_5 CBB0",                           f"@{CBB0_TPMI}.sst_pp_info_5.read()"),
    ("SST_PP_INFO_6 CBB0",                           f"@{CBB0_TPMI}.sst_pp_info_6.read()"),
    ("SST_PP_INFO_7 CBB0",                           f"@{CBB0_TPMI}.sst_pp_info_7.read()"),
    ("SST_PP_INFO_8 CBB0",                           f"@{CBB0_TPMI}.sst_pp_info_8.read()"),
    ("SST_PP_CONTROL CBB0",                          f"@{CBB0_TPMI}.sst_pp_control.read()"),
    ("SST_PP_STATUS CBB0",                           f"@{CBB0_TPMI}.sst_pp_status.read()"),
    ("FIT_CONFIG_0 CBB0",                            f"@{CBB0_TPMI}.fit_config_0.read()"),
    ("FIT_CONFIG_1 CBB0",                            f"@{CBB0_TPMI}.fit_config_1.read()"),
    ("PLR_DIE_LEVEL CBB0",                           f"@{CBB0_TPMI}.plr_die_level.read()"),
    ("PLR_DIE_LEVEL CBB1",                           f"@{CBB1_TPMI}.plr_die_level.read()"),
    ("GPSB HWP_REQUEST CBB0 pma0",                  f"@{CBB0_GPSB}.hwp_request.read()"),
    ("GPSB HWP_REQUEST_RESOLVED CBB0 pma0",         f"@{CBB0_GPSB}.hwp_request_resolved.read()"),
    ("PLR MAILBOX IMH0 (high-level clipping)",       f"@{IMH_FSMS}.plr_mailbox_data.read()"),
    ("PLR MAILBOX CBB0 (high-level clipping)",       f"@{CBB0_TPMI}.plr_mailbox_data.read()"),
])

# ═══════════════════════════════════════════════════════════════
# CPU RAPL / POWER
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "CPU_RAPL", [
    ("PEM_CONTROL CBB0 (RAPL PEM config)",           f"@{CBB0_TPMI}.pem_control.read()"),
    ("PEM_STATUS CBB0 (RAPL PEM status)",            f"@{CBB0_TPMI}.pem_status.read()"),
    ("PEM_CONTROL CBB1",                             f"@{CBB1_TPMI}.pem_control.read()"),
    ("PEM_STATUS CBB1",                              f"@{CBB1_TPMI}.pem_status.read()"),
    ("SOCKET_RAPL_POWER_UNIT IMH0",                  f"@{CBB0_TPMI}.socket_rapl_power_unit.read()"),
    ("SOCKET_RAPL_ENERGY_STATUS IMH0",               f"@{CBB0_TPMI}.socket_rapl_energy_status.read()"),
    ("PLR MAILBOX IMH0",                             f"@{IMH_FSMS}.plr_mailbox_data.read()"),
    ("PLR MAILBOX CBB0",                             f"@{CBB0_TPMI}.plr_mailbox_data.read()"),
])

# ═══════════════════════════════════════════════════════════════
# PMAX / SIMPL / RACL
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "PMAX_SIMPL_RACL", [
    ("PEM_CONTROL CBB0",                             f"@{CBB0_TPMI}.pem_control.read()"),
    ("PEM_STATUS CBB0",                              f"@{CBB0_TPMI}.pem_status.read()"),
    ("PLR_DIE_LEVEL CBB0",                           f"@{CBB0_TPMI}.plr_die_level.read()"),
    ("PLR MAILBOX IMH0",                             f"@{IMH_FSMS}.plr_mailbox_data.read()"),
    ("PLR MAILBOX CBB0",                             f"@{CBB0_TPMI}.plr_mailbox_data.read()"),
])

# ═══════════════════════════════════════════════════════════════
# THERMAL MANAGEMENT (CCF_GV + CPU Thermal)
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "Thermal_Management", [
    ("OPC_THERMAL_MONITOR CBB0",                     f"@{CBB0_TPMI}.opc_thermal_monitor.read()"),
    ("OPC_HWP_CAPABILITY CBB0",                     f"@{CBB0_TPMI}.opc_hwp_capability.read()"),
    ("OPC_HWP_CONTROLS CBB0",                       f"@{CBB0_TPMI}.opc_hwp_controls.read()"),
    ("UFS_CONTROL CBB0 (CCF GV freq control)",       f"@{CBB0_TPMI}.ufs_control.read()"),
    ("UFS_STATUS CBB0 (CCF GV freq status)",         f"@{CBB0_TPMI}.ufs_status.read()"),
    ("PROCHOT_RESPONSE_POWER CBB0",                  f"@{CBB0_TPMI}.prochot_response_power.read()"),
    ("PLR_DIE_LEVEL CBB0",                           f"@{CBB0_TPMI}.plr_die_level.read()"),
    ("GPSB HWRS_DIE_STATUS CBB0 pma0",              f"@{CBB0_GPSB}.hwrs_die_status.read()"),
    ("GPSB HWRS_SEQ_CONTROL CBB0 pma0",             f"@{CBB0_GPSB}.hwrs_seq_control.read()"),
    ("GPSB MC_STATUS CBB0 pma0",                    f"@{CBB0_GPSB}.mc_status.read()"),
])

# ═══════════════════════════════════════════════════════════════
# FABRIC DVFS (UFS / CCF GV)
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "Fabric_DVFS", [
    ("UFS_CONTROL CBB0 (uncore freq scaling ctrl)",  f"@{CBB0_TPMI}.ufs_control.read()"),
    ("UFS_STATUS CBB0 (current voltage/freq)",       f"@{CBB0_TPMI}.ufs_status.read()"),
    ("UFS_CONTROL CBB1",                             f"@{CBB1_TPMI}.ufs_control.read()"),
    ("UFS_STATUS CBB1",                              f"@{CBB1_TPMI}.ufs_status.read()"),
    ("PLATFORM_INFO IMH0 (P1 ratio)",                f"@{IMH_IOREGS}.platform_info.read()"),
])

# ═══════════════════════════════════════════════════════════════
# SST (PCT / sst_pp / sst_tf)
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "SST", [
    ("SST_PP_CONTROL CBB0",                          f"@{CBB0_TPMI}.sst_pp_control.read()"),
    ("SST_PP_STATUS CBB0",                           f"@{CBB0_TPMI}.sst_pp_status.read()"),
    ("SST_PP_INFO_11 CBB0 (P0/P1/Pm ratios)",       f"@{CBB0_TPMI}.sst_pp_info_11.read()"),
    ("SST_PP_HEADER CBB0",                           f"@{CBB0_TPMI}.sst_pp_header.read()"),
    ("SST_PP_INFO_0 CBB0",                           f"@{CBB0_TPMI}.sst_pp_info_0.read()"),
    ("PP1_SST_PP_INFO_11 CBB0",                      f"@{CBB0_TPMI}.pp1_sst_pp_info_11.read()"),
])

# ═══════════════════════════════════════════════════════════════
# IMH0 uncore telem (shared across features)
# ═══════════════════════════════════════════════════════════════
sweep_feature(s, "IMH0_Telemetry", [
    ("UNCORE_TELEM IMH0 [0:9] (first 10 slots)",
     "@[sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_telem[i].read() for i in range(10)]"),
])

s.close()

# Save results JSON
with open(OUT_JSON, "w") as f:
    json.dump(RESULTS, f, indent=2)
print(f"\nResults saved to {OUT_JSON}")

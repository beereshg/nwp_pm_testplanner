"""
sweep_comprehensive.py — Full NWP PM register sweep, feature-batched.
Covers all meaningful registers from:
  - CBB0/CBB1 base.tpmi  (278 non-reserved registers each)
  - CBB0 punit_pmsb.pmsb_pcu
  - IMH0 ptpcfsms.ptpcfsms
  - IMH0 ptpcfsms_pmsb.ptpcfsms_pmsb
  - IMH0 ptpcioregs.ptpcioregs
  - CBB0 GPSB pma0 (234 registers)

NIO OSXML IPs (nwp_imh extern_ips_v1_0.xml):
  punit, hwrs, rc, ra, svid, pmax, oobmsm, mc, mse, ddrio, ubox, hiop, npk

Usage:
  python sweep_comprehensive.py --output <stem>   # saves <stem>.json + <stem>.html
  python sweep_comprehensive.py --batch RAPL       # sweep only RAPL feature batch
  python sweep_comprehensive.py --list-batches     # list available batches

Runs against localhost:4444 telnet-frontend tunnel.
"""
import socket, time, re, json, datetime, sys, os

# ── CLI args ────────────────────────────────────────────────────────────────
stem = "sweep_comprehensive"
batch_filter = None
if "--output" in sys.argv:
    stem = sys.argv[sys.argv.index("--output") + 1]
if "--batch" in sys.argv:
    batch_filter = sys.argv[sys.argv.index("--batch") + 1]
if "--list-batches" in sys.argv:
    print("Available batches: RAPL, SST, PLR, UFS, OPC_HWP, PMAX, FIT, THERMAL, GPSB, PMSB, PTPCIOREGS, PTPCFSMS, OOBMSM, DRC, SVID, C_STATE, MISC")
    sys.exit(0)

OUT_JSON = os.path.join(os.path.dirname(__file__), stem + ".json")
RESULTS = {"timestamp": datetime.datetime.now().isoformat(), "stem": stem, "features": {}}

# ── Paths ───────────────────────────────────────────────────────────────────
CBB0 = "sv.socket0.cbb0.base.tpmi"
CBB1 = "sv.socket0.cbb1.base.tpmi"
PMSB0 = "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu"
PMSB1 = "sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu"
FSMS = "sv.socket0.imh0.punit.ptpcfsms.ptpcfsms"
FSMS_PMSB = "sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb"
IOREGS = "sv.socket0.imh0.punit.ptpcioregs.ptpcioregs"
GPSB0 = "sv.socket0.cbb0.compute0.getbypath('pma0').gpsb"
GPSB1 = "sv.socket0.cbb1.compute0.getbypath('pma0').gpsb"


def simics_cmd(s, cmd, wait=2):
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    s.settimeout(1.5)
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


def read_reg(s, label, cmd, wait=2):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l
             and not l.startswith(cmd[:15])]
    value = "\n".join(lines).strip()
    status = "error" if any(x in value for x in ["Error", "Traceback", "AttributeError", "NameError", "SyntaxError"]) else "ok"
    path = cmd.replace("@", "").replace(".read()", "").strip()
    nonzero = status == "ok" and value not in ("0x0", "", "0")
    tag = "NZ" if nonzero else "  "
    print(f"  [{tag}] {label[:55]}: {value[:60]}")
    return {"label": label, "path": path, "value": value, "status": status, "nonzero": nonzero}


def sweep(s, name, regs):
    if batch_filter and batch_filter.upper() not in name.upper():
        return
    print(f"\n{'='*60}\n  {name}\n{'='*60}")
    RESULTS["features"][name] = [read_reg(s, lbl, cmd) for lbl, cmd in regs]


def R(path, reg, label=None):
    """Helper: build (label, @path.reg.read()) tuple."""
    lbl = label or reg.replace("_", " ").title()
    return (lbl, f"@{path}.{reg}.read()")


def both_cbb(reg, label=None):
    """Read same reg from CBB0 and CBB1."""
    lbl = label or reg.replace("_", " ").title()
    return [
        (f"{lbl} CBB0", f"@{CBB0}.{reg}.read()"),
        (f"{lbl} CBB1", f"@{CBB1}.{reg}.read()"),
    ]


# ── Connect ─────────────────────────────────────────────────────────────────
s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

# ════════════════════════════════════════════════════════════════════════════
# BATCH 1: RAPL — Socket / DRAM / Platform
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "RAPL_Socket", [
    *both_cbb("socket_rapl_domain_header"),
    *both_cbb("socket_rapl_power_unit"),
    *both_cbb("socket_rapl_pl_info"),
    *both_cbb("socket_rapl_pl1_control"),
    *both_cbb("socket_rapl_pl2_control"),
    *both_cbb("socket_rapl_pl4_control"),
    *both_cbb("socket_rapl_energy_status"),
    *both_cbb("socket_rapl_perf_status"),
    *both_cbb("rapl_energy_report"),
    R(GPSB0, "package_rapl_limit", "Package RAPL Limit GPSB"),
    R(GPSB0, "package_rapl_perf_status", "Package RAPL Perf Status"),
    R(GPSB0, "package_power_sku", "Package Power SKU"),
    R(GPSB0, "package_power_sku_unit", "Package Power SKU Unit"),
    R(GPSB0, "package_energy_status", "Package Energy Status"),
])

sweep(s, "RAPL_DRAM", [
    *both_cbb("dram_rapl_domain_header"),
    *both_cbb("dram_rapl_power_unit"),
    *both_cbb("dram_rapl_pl_info"),
    *both_cbb("dram_rapl_pl1_control"),
    *both_cbb("dram_rapl_energy_status"),
    *both_cbb("dram_rapl_perf_status"),
    R(GPSB0, "dram_energy_status", "DRAM Energy Status GPSB"),
    R(GPSB0, "dram_rapl_perf_status_cfg", "DRAM RAPL Perf Status CFG"),
])

sweep(s, "RAPL_Platform", [
    *both_cbb("platform_rapl_domain_header"),
    *both_cbb("platform_rapl_power_unit"),
    *both_cbb("platform_rapl_pl_info"),
    *both_cbb("platform_rapl_pl1_control"),
    *both_cbb("platform_rapl_pl2_control"),
    *both_cbb("platform_rapl_energy_status"),
    *both_cbb("platform_rapl_perf_status"),
    R(GPSB0, "platform_rapl_limit", "Platform RAPL Limit"),
    R(GPSB0, "platform_energy_status", "Platform Energy Status"),
    R(GPSB0, "platform_power_info", "Platform Power Info"),
    R(GPSB0, "primary_plane_turbo_power_limit", "Primary Plane Turbo Power Limit"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 2: PEM (Power Excursion Monitor — SIMPL/RACL)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "PEM_SIMPL_RACL", [
    *both_cbb("pem_header"),
    *both_cbb("pem_control"),
    *both_cbb("pem_status"),
    *both_cbb("pem_pmt_info"),
    *both_cbb("pfm_header"),
    *both_cbb("pfm_control"),
    *both_cbb("pfm_status"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 3: PMAX
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "PMAX", [
    *both_cbb("pmax_header"),
    *both_cbb("pmax_control"),
    *both_cbb("pmax_status"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 4: PLR (Perf Limit Reasons)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "PLR", [
    *both_cbb("plr_header"),
    *both_cbb("plr_die_level"),
    *both_cbb("plr_mailbox_interface"),
    *both_cbb("plr_mailbox_data"),
    R(PMSB0, "acp_perf_limit", "ACP Perf Limit CBB0 (all FIDs)"),
    R(PMSB1, "acp_perf_limit", "ACP Perf Limit CBB1 (all FIDs)"),
    R(FSMS_PMSB, "acp_perf_limit", "ACP Perf Limit IMH0"),
    R(GPSB0, "ia_perf_limit_reasons2", "IA Perf Limit Reasons2 GPSB"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 5: OPC / HWP
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "OPC_HWP", [
    *both_cbb("opc_header"),
    *both_cbb("opc_hwp_capability"),
    *both_cbb("opc_hwp_controls"),
    *both_cbb("opc_pkg_therm_status"),
    *both_cbb("opc_pkgc_entry_control"),
    *both_cbb("opc_dimm_temps_0"),
    *both_cbb("opc_dimm_temps_1"),
    *both_cbb("opc_dimm_temps_2"),
    *both_cbb("opc_dimm_temps_3"),
    R(FSMS, "opc_hwp_controls", "OPC HWP Controls IMH0 FSMS"),
    R(GPSB0, "hwp_capabilities", "HWP Capabilities GPSB"),
    R(GPSB0, "hwp_request", "HWP Request GPSB"),
    R(GPSB0, "hwp_request_pkg", "HWP Request PKG GPSB"),
    R(GPSB0, "hwp_status", "HWP Status GPSB"),
    R(GPSB0, "hwp_interrupt", "HWP Interrupt GPSB"),
    R(GPSB0, "hwp_peci_request_info", "HWP PECI Request Info GPSB"),
    R(GPSB0, "pm_enable", "PM Enable GPSB"),
    ("GPSB HWP_REQUEST pma0 (per-FID)",
     "@sv.socket0.cbb0.compute0.getbypath('pma0').gpsb.hwp_request.read()"),
    ("GPSB HWP_REQUEST_RESOLVED pma0",
     "@sv.socket0.cbb0.compute0.getbypath('pma0').gpsb.hwp_request_resolved.read()"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 6: SST (Performance Profiles — all 5 PPs, TF, BF, CP, CLOS)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "SST_PP_Current", [
    *both_cbb("sst_header"),
    *both_cbb("sst_pp_header"),
    *both_cbb("sst_pp_control"),
    *both_cbb("sst_pp_status"),
    *both_cbb("sst_pp_misc_control"),
    *both_cbb("sst_pp_misc_status"),
    *both_cbb("sst_pp_info_0"),
    *both_cbb("sst_pp_info_1"),
    *both_cbb("sst_pp_info_2"),
    *both_cbb("sst_pp_info_3"),
    *both_cbb("sst_pp_info_4"),
    *both_cbb("sst_pp_info_5"),
    *both_cbb("sst_pp_info_6"),
    *both_cbb("sst_pp_info_7"),
    *both_cbb("sst_pp_info_8"),
    *both_cbb("sst_pp_info_9"),
    *both_cbb("sst_pp_info_10"),
    *both_cbb("sst_pp_info_11"),
    *both_cbb("sst_pp_info_12"),
    *both_cbb("sst_pp_info_13"),
    *both_cbb("sst_pp_offset_0"),
    *both_cbb("sst_pp_offset_1"),
])

sweep(s, "SST_TF_BF", [
    *both_cbb("sst_bf_info_0"),
    *both_cbb("sst_bf_info_1"),
    *both_cbb("sst_tf_info_0"),
    *both_cbb("sst_tf_info_1"),
    *both_cbb("sst_tf_info_2"),
    *both_cbb("sst_tf_info_3"),
    *both_cbb("sst_tf_info_4"),
    *both_cbb("sst_tf_info_5"),
    *both_cbb("sst_tf_info_6"),
    *both_cbb("sst_tf_info_7"),
    *both_cbb("sst_tf_info_8"),
    *both_cbb("sst_tf_info_9"),
])

sweep(s, "SST_CP_CLOS", [
    *both_cbb("sst_cp_header"),
    *both_cbb("sst_cp_control"),
    *both_cbb("sst_cp_status"),
    *both_cbb("sst_clos_assoc_0"),
    *both_cbb("sst_clos_assoc_1"),
    *both_cbb("sst_clos_assoc_2"),
    *both_cbb("sst_clos_assoc_3"),
    *both_cbb("sst_clos_config_0"),
    *both_cbb("sst_clos_config_1"),
    *both_cbb("sst_clos_config_2"),
    *both_cbb("sst_clos_config_3"),
])

sweep(s, "SST_PP1_Profile", [
    *both_cbb("pp1_sst_pp_info_0"),
    *both_cbb("pp1_sst_pp_info_4"),
    *both_cbb("pp1_sst_pp_info_11"),
    *both_cbb("pp1_sst_bf_info_0"),
    *both_cbb("pp1_sst_tf_info_0"),
    *both_cbb("pp1_sst_tf_info_2"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 7: UFS / Fabric DVFS (CBB TPMI)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "UFS_Fabric_DVFS", [
    *both_cbb("ufs_header"),
    *both_cbb("ufs_control"),
    *both_cbb("ufs_status"),
    *both_cbb("ufs_adv_control_1"),
    *both_cbb("ufs_adv_control_2"),
    *both_cbb("ufs_fabric_cluster_offset"),
    ("UFS_CONTROL Fabric1 CBB0", f"@{CBB0}.ufs_control_fabric_1.read()"),
    ("UFS_STATUS Fabric1 CBB0", f"@{CBB0}.ufs_status_fabric_1.read()"),
    ("UFS_ADV_CONTROL_1 Fabric1 CBB0", f"@{CBB0}.ufs_adv_control_1_fabric_1.read()"),
    ("UFS_ADV_CONTROL_2 Fabric1 CBB0", f"@{CBB0}.ufs_adv_control_2_fabric_1.read()"),
    R(FSMS, "ufs_control", "UFS Control IMH0 FSMS"),
    R(FSMS, "ufs_status", "UFS Status IMH0 FSMS"),
    R(FSMS, "ufs_adv_control_1", "UFS Adv Control 1 IMH0"),
    R(FSMS, "ufs_adv_control_2", "UFS Adv Control 2 IMH0"),
    R(FSMS, "ufs_fabric_cluster_offset", "UFS Fabric Cluster Offset IMH0"),
    R(FSMS, "uncore_ratio_limit", "Uncore Ratio Limit IMH0"),
    R(FSMS, "uncore_configuration", "Uncore Configuration IMH0"),
    R(FSMS, "uncore_perf_status", "Uncore Perf Status IMH0"),
    R(GPSB0, "uncore_ratio_limit", "Uncore Ratio Limit GPSB"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 8: Thermal (OPC thermal, prochot, temperature, SVID)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "Thermal_Prochot", [
    *both_cbb("opc_thermal_monitor"),
    *both_cbb("prochot_response_power"),
    *both_cbb("stat_temphot_cfg"),
    *both_cbb("stat_temptrip"),
    *both_cbb("temperature_target"),
    *both_cbb("temperature_target_cfg"),
    *both_cbb("thermtrip_config_cfg"),
    R(GPSB0, "package_temperature", "Package Temperature GPSB"),
    R(GPSB0, "pp0_temperature", "PP0 Temperature GPSB"),
    R(GPSB0, "package_therm_margin", "Package Therm Margin GPSB"),
    R(GPSB0, "therm_event_ffm", "Therm Event FFM GPSB"),
    R(GPSB0, "mcp_thermal_report_1", "MCP Thermal Report 1"),
    R(GPSB0, "mcp_thermal_report_2", "MCP Thermal Report 2"),
    R(GPSB0, "mem_trml_temperature_report", "Mem Thermal Temperature Report"),
    R(FSMS, "vr_current_config", "VR Current Config IMH0"),
    R(FSMS, "vr_misc_config", "VR Misc Config IMH0"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 9: FIT (Fine-grained Turbo)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "FIT_Turbo", [
    *both_cbb("fit_config_0"),
    *both_cbb("fit_config_1"),
    *both_cbb("fit_info_0"),
    *both_cbb("odc_header"),
    *both_cbb("odc_turbo_max_ratio"),
    *both_cbb("odc_trl_ratios"),
    *both_cbb("odc_trl_numcores"),
    R(GPSB0, "turbo_activation_ratio", "Turbo Activation Ratio GPSB"),
    R(GPSB0, "turbo_ratio_limit_ratios", "Turbo Ratio Limit Ratios GPSB"),
    R(GPSB0, "turbo_ratio_limit_groups", "Turbo Ratio Limit Groups GPSB"),
    R(GPSB0, "dynamic_perf_power_ctl_cfg", "Dynamic Perf Power Ctl CFG"),
    R(GPSB0, "p_state_limits_cfg", "P-State Limits CFG"),
    R(GPSB0, "rp_state_limits_cfg", "RP State Limits CFG"),
    R(FSMS, "sst_pp_info_4", "SST_PP_INFO_4 IMH0 FSMS"),
    R(FSMS, "sst_pp_info_11", "SST_PP_INFO_11 IMH0 FSMS"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 10: SVID
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "SVID", [
    *both_cbb("svid_config"),
    R(GPSB0, "svid_1_30_0_cfg", "SVID Config GPSB"),
    R(FSMS, "svid_config", "SVID Config IMH0 FSMS"),
    R(FSMS, "vr_current_config_cfg", "VR Current Config CFG IMH0"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 11: GPSB — C-States, Platform, RAPL, Turbo
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "GPSB_CState_Platform", [
    R(GPSB0, "c_state_latency_control", "C-State Latency Control"),
    R(GPSB0, "c2_ddr_tt", "C2 DDR Timing"),
    R(GPSB0, "c2c3tt_cfg", "C2C3 Timing CFG"),
    R(GPSB0, "pc2_rcntr", "PC2 Residency Counter"),
    R(GPSB0, "pc3_rcntr", "PC3 Residency Counter"),
    R(GPSB0, "pc6_rcntr", "PC6 Residency Counter"),
    R(GPSB0, "pc7_rcntr", "PC7 Residency Counter"),
    R(GPSB0, "platform_info", "Platform Info (max/min non-turbo ratio)"),
    R(GPSB0, "pst_config_control", "PST Config Control"),
    R(GPSB0, "energy_perf_bias_config", "Energy Perf Bias Config (EPB)"),
    R(GPSB0, "io_bandwidth_p_limit_control", "IO BW P-Limit Control"),
    R(GPSB0, "io_bw_p_limit_override", "IO BW P-Limit Override"),
    R(GPSB0, "pcode_config", "PCode Config"),
    R(GPSB0, "sapmctl_cfg", "SAPM Control CFG"),
    R(GPSB0, "freq_clos_config", "Freq CLOS Config"),
    R(GPSB0, "freq_clos0_config", "Freq CLOS0 Config"),
    R(GPSB0, "freq_clos1_config", "Freq CLOS1 Config"),
    R(GPSB0, "pair_weight_override", "Pair Weight Override"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 12: IMH0 PMSB registers (ptpcfsms_pmsb)
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "IMH0_PMSB", [
    R(FSMS_PMSB, "acp_perf_limit", "ACP Perf Limit (fid_0)"),
    R(FSMS_PMSB, "core_electrical_req", "Core Electrical Req"),
    R(FSMS_PMSB, "core_pm_event", "Core PM Event"),
    R(FSMS_PMSB, "uncore_virtual_sig", "Uncore Virtual Signal"),
    R(FSMS_PMSB, "uncore_telem", "Uncore Telem [first 500 slots]"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 13: IMH0 FSMS — power_ctl, opc_hwp_controls, SST, SAPM
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "IMH0_FSMS_Power", [
    R(FSMS, "power_ctl1", "Power CTL1 IMH0"),
    R(FSMS, "opc_hwp_controls", "OPC HWP Controls IMH0"),
    R(FSMS, "plr_mailbox_interface", "PLR Mailbox Interface IMH0"),
    R(FSMS, "plr_mailbox_data", "PLR Mailbox Data IMH0"),
    R(FSMS, "sst_pp_info_0", "SST PP Info 0 IMH0"),
    R(FSMS, "sst_pp_info_4", "SST PP Info 4 (TRL) IMH0"),
    R(FSMS, "sst_pp_info_11", "SST PP Info 11 (P0/P1/Pm) IMH0"),
    R(FSMS, "sst_pp_control", "SST PP Control IMH0"),
    R(FSMS, "sst_pp_status", "SST PP Status IMH0"),
    R(FSMS, "sst_tf_info_0", "SST TF Info 0 IMH0"),
    R(FSMS, "sst_tf_info_2", "SST TF Info 2 IMH0"),
    R(FSMS, "uncore_telemetry_mapping", "Uncore Telemetry Mapping"),
    R(FSMS, "uncore_fivr_err_log_cfg", "Uncore FIVR Error Log CFG"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 14: OOBMSM Telemetry params
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "OOBMSM_Telemetry", [
    *both_cbb("oobmsm_telem_params_0"),
    *both_cbb("oobmsm_telem_params_1"),
    *both_cbb("oobmsm_telem_params_2"),
    *both_cbb("oobmsm_telem_params_3"),
    *both_cbb("oobmsm_telem_params_4"),
    *both_cbb("oobmsm_telem_params_5"),
    *both_cbb("oobmsm_telem_params_6"),
    *both_cbb("oobmsm_telem_params_7"),
    *both_cbb("oobmsm_telem_params_8"),
    R(GPSB0, "package_energy_time_status", "Package Energy+Time Status"),
])

# ════════════════════════════════════════════════════════════════════════════
# BATCH 15: DRC / MISC / Security
# ════════════════════════════════════════════════════════════════════════════
sweep(s, "DRC_MISC", [
    *both_cbb("drc_header"),
    *both_cbb("drc_control"),
    *both_cbb("drc_status"),
    *both_cbb("drc_config0"),
    *both_cbb("drc_config1"),
    *both_cbb("ia32_misc_package_ctls"),
    *both_cbb("interface_select"),
    *both_cbb("overclocking_mailbox"),
    *both_cbb("overclocking_secure_status"),
    R(GPSB0, "pcu_misc_enables2", "PCU Misc Enables 2"),
    R(GPSB0, "pcu_dfx_ctrl2", "PCU DFX Ctrl 2"),
    R(GPSB0, "llc_config", "LLC Config"),
    R(GPSB0, "llc_structure", "LLC Structure"),
    R(GPSB0, "global_nid_socket_0_to_3_map", "Global NID Socket Map"),
    R(GPSB0, "die_config", "Die Config"),
    R(GPSB0, "turbo_activation_ratio", "Turbo Activation Ratio"),
])

# ════════════════════════════════════════════════════════════════════════════
# Close and save
# ════════════════════════════════════════════════════════════════════════════
s.close()

# Count stats
total = sum(len(v) for v in RESULTS["features"].values())
ok = sum(1 for v in RESULTS["features"].values() for r in v if r["status"] == "ok")
nz = sum(1 for v in RESULTS["features"].values() for r in v if r.get("nonzero"))
print(f"\nTotal: {total} registers | OK: {ok} | Non-zero: {nz}")

with open(OUT_JSON, "w") as f:
    json.dump(RESULTS, f, indent=2)
print(f"Saved: {OUT_JSON}")

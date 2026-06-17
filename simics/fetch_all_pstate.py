import socket, time, re

PMSB_CBB0 = "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu"
PMSB_CBB1 = "sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu"
PMSB_IMH  = "sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb"
PTPCFSMS  = "sv.socket0.imh0.punit.ptpcfsms.ptpcfsms"
PTPCIOREGS= "sv.socket0.imh0.punit.ptpcioregs.ptpcioregs"
TPMI_CBB0 = "sv.socket0.cbb0.base.tpmi"
TPMI_CBB1 = "sv.socket0.cbb1.base.tpmi"


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


def run(label, cmd, wait=3):
    r = simics_cmd(s, cmd, wait)
    print(f"\n{'='*64}")
    print(f"  {label}")
    print(f"{'='*64}")
    print(r)


s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1)
s.recv(4096)

# ── Previously verified PMSB reads ─────────────────────────────────────────
run("ACP_PERF_LIMIT CBB0 (all FIDs)",
    "@" + PMSB_CBB0 + ".acp_perf_limit.read()")
run("ACP_PERF_LIMIT CBB1 (all FIDs)",
    "@" + PMSB_CBB1 + ".acp_perf_limit.read()")
run("ACP_PERF_LIMIT IMH0",
    "@" + PMSB_IMH + ".acp_perf_limit.read()")
run("CORE_ELECTRICAL_REQ IMH0",
    "@" + PMSB_IMH + ".core_electrical_req.read()")
run("CORE_PM_EVENT IMH0",
    "@" + PMSB_IMH + ".core_pm_event.read()")
run("UNCORE_VIRTUAL_SIG IMH0",
    "@" + PMSB_IMH + ".uncore_virtual_sig.read()")

# ── IMH0 ptpcioregs — Platform Info and EPB ────────────────────────────────
run("PLATFORM_INFO IMH0 (max/min non-turbo ratio fused)",
    "@" + PTPCIOREGS + ".platform_info.read()")
run("ENERGY_PERF_BIAS_CONFIG IMH0 (EPB)",
    "@" + PTPCIOREGS + ".energy_perf_bias_config.read()")

# ── IMH0 ptpcfsms — SST P-State ratio info ─────────────────────────────────
run("SST_PP_INFO_11 IMH0 (P0/P1/Pm core ratios)",
    "@" + PTPCFSMS + ".sst_pp_info_11.read()")
run("SST_PP_INFO_4 IMH0 (TRL ratio 0)",
    "@" + PTPCFSMS + ".sst_pp_info_4.read()")
run("SST_PP_INFO_5 IMH0",
    "@" + PTPCFSMS + ".sst_pp_info_5.read()")

# ── CBB0 TPMI — HWP controls and capabilities ──────────────────────────────
run("OPC_HWP_CAPABILITY CBB0 (guaranteed/max/min/efficient ratio)",
    "@" + TPMI_CBB0 + ".opc_hwp_capability.read()")
run("OPC_HWP_CONTROLS CBB0 (HWP enable, OOB mode)",
    "@" + TPMI_CBB0 + ".opc_hwp_controls.read()")
run("OPC_HWP_CAPABILITY CBB1",
    "@" + TPMI_CBB1 + ".opc_hwp_capability.read()")
run("OPC_HWP_CONTROLS CBB1",
    "@" + TPMI_CBB1 + ".opc_hwp_controls.read()")

# ── CBB0 TPMI — UFS / Uncore Frequency Scaling ─────────────────────────────
run("UFS_STATUS CBB0 (current uncore voltage/freq)",
    "@" + TPMI_CBB0 + ".ufs_status.read()")
run("UFS_STATUS CBB1",
    "@" + TPMI_CBB1 + ".ufs_status.read()")

# ── CBB0 TPMI — SST P-state ratio info ─────────────────────────────────────
run("SST_PP_INFO_11 CBB0 (P0/P1/Pm core ratios)",
    "@" + TPMI_CBB0 + ".sst_pp_info_11.read()")
run("SST_PP_INFO_4 CBB0 (TRL ratio_0)",
    "@" + TPMI_CBB0 + ".sst_pp_info_4.read()")
run("SST_PP_INFO_5 CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_info_5.read()")
run("SST_PP_INFO_6 CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_info_6.read()")
run("SST_PP_INFO_7 CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_info_7.read()")
run("SST_PP_INFO_8 CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_info_8.read()")
run("SST_PP_CONTROL CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_control.read()")
run("SST_PP_STATUS CBB0",
    "@" + TPMI_CBB0 + ".sst_pp_status.read()")

# ── CBB0 TPMI — FIT config ─────────────────────────────────────────────────
run("FIT_CONFIG_0 CBB0 (fine-grained turbo config)",
    "@" + TPMI_CBB0 + ".fit_config_0.read()")
run("FIT_CONFIG_1 CBB0",
    "@" + TPMI_CBB0 + ".fit_config_1.read()")

# ── CBB0 TPMI — PLR die level ──────────────────────────────────────────────
run("PLR_DIE_LEVEL CBB0 (die-level perf limit reasons)",
    "@" + TPMI_CBB0 + ".plr_die_level.read()")
run("PLR_DIE_LEVEL CBB1",
    "@" + TPMI_CBB1 + ".plr_die_level.read()")

# ── CBB0 GPSB — HWP request per module ────────────────────────────────────
run("GPSB HWP_REQUEST CBB0 module0 (PMA0 per-module HWP request)",
    "@sv.socket0.cbb0.compute0.getbypath('pma0').gpsb.hwp_request.read()")
run("GPSB HWP_REQUEST_RESOLVED CBB0 module0 (resolved/granted HWP)",
    "@sv.socket0.cbb0.compute0.getbypath('pma0').gpsb.hwp_request_resolved.read()")

# ── PLR mailbox ─────────────────────────────────────────────────────────────
print(f"\n{'='*64}")
print("  PLR High-Level Clipping — IMH0 (domain=2)")
print(f"{'='*64}")
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.command.write(0)", wait=1)
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.domain.write(2)", wait=1)
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.run_busy.write(1)", wait=2)
print(simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_data.read()", wait=2))

print(f"\n{'='*64}")
print("  PLR High-Level Clipping — CBB0 (domain=2)")
print(f"{'='*64}")
simics_cmd(s, "@" + TPMI_CBB0 + ".plr_mailbox_interface.command.write(0)", wait=1)
simics_cmd(s, "@" + TPMI_CBB0 + ".plr_mailbox_interface.domain.write(2)", wait=1)
simics_cmd(s, "@" + TPMI_CBB0 + ".plr_mailbox_interface.run_busy.write(1)", wait=2)
print(simics_cmd(s, "@" + TPMI_CBB0 + ".plr_mailbox_data.read()", wait=2))

s.close()
print("\nDone.")



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


def run(label, cmd, wait=3):
    r = simics_cmd(s, cmd, wait)
    print(f"\n{'='*64}")
    print(f"  {label}")
    print(f"{'='*64}")
    print(r)


s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1)
s.recv(4096)

# Discover correct core path first
run("DISCOVER: cbb0.compute0 nodenames", "@print(sv.socket0.cbb0.compute0.nodenames)", wait=3)
run("DISCOVER: cbb0 nodenames (top-level)", "@print(sv.socket0.cbb0.nodenames)", wait=3)

# ── PMSB Namednodes Reads ───────────────────────────────────────────────────
run("ACP_PERF_LIMIT CBB0 (all FIDs read-clears 0x0=no limiting)",
    "@" + PMSB_CBB.format("cbb0") + ".acp_perf_limit.read()")
run("ACP_PERF_LIMIT CBB1 (all FIDs read-clears)",
    "@" + PMSB_CBB.format("cbb1") + ".acp_perf_limit.read()")
run("ACP_PERF_LIMIT IMH0 (fid_0  0x0=no limiting)",
    "@" + PMSB_IMH + ".acp_perf_limit.read()")
run("CORE_ELECTRICAL_REQ IMH0 (power/current electrical budget signals)",
    "@" + PMSB_IMH + ".core_electrical_req.read()")
run("CORE_PM_EVENT IMH0 (core power-management events)",
    "@" + PMSB_IMH + ".core_pm_event.read()")
run("UNCORE_TELEM IMH0 (uncore telemetry)",
    "@" + PMSB_IMH + ".uncore_telem.read()")
run("UNCORE_VIRTUAL_SIG IMH0 (virtual signal aggregation)",
    "@" + PMSB_IMH + ".uncore_virtual_sig.read()")

# ── PLR Mailbox Reads ───────────────────────────────────────────────────────
print(f"\n{'='*64}")
print("  PLR High-Level Clipping Reasons  IMH0 (domain=2)")
print(f"{'='*64}")
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.command.write(0)", wait=1)
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.domain.write(2)", wait=1)
simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_interface.run_busy.write(1)", wait=2)
print(simics_cmd(s, "@" + PTPCFSMS + ".plr_mailbox_data.read()", wait=2))

print(f"\n{'='*64}")
print("  PLR High-Level Clipping Reasons  CBB0 (domain=2)")
print(f"{'='*64}")
simics_cmd(s, "@" + TPMI_CBB.format("cbb0") + ".plr_mailbox_interface.command.write(0)", wait=1)
simics_cmd(s, "@" + TPMI_CBB.format("cbb0") + ".plr_mailbox_interface.domain.write(2)", wait=1)
simics_cmd(s, "@" + TPMI_CBB.format("cbb0") + ".plr_mailbox_interface.run_busy.write(1)", wait=2)
print(simics_cmd(s, "@" + TPMI_CBB.format("cbb0") + ".plr_mailbox_data.read()", wait=2))

s.close()
print("\nDone.")

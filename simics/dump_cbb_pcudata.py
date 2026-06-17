"""
Dump CBB pcudata (punit registers) for CBB0 and CBB1 on NWP Simics.
Shows key PM registers: ccp_status, ccf_wp_status, dfx_ctrl, ring_distress,
acp_perf_limit, ufs_control, ufs_status, and TPMI overview.
Usage: @exec(open('/nfs/site/disks/simcloud_bg3_001/nwp_python310/newport/dump_cbb_pcudata.py').read())
"""
import namednodes as n

def sr(obj):
    try:
        return hex(int(obj)) if obj is not None else "N/A"
    except:
        return str(obj)

def dump_reg(path, name, val):
    print(f"    {name:<50} = {sr(val)}")

def dump_cbb(cbb_name):
    die = getattr(n.sv.socket0, cbb_name)
    print(f"\n{'='*70}")
    print(f"  {cbb_name.upper()} PCUDATA DUMP")
    print(f"{'='*70}")

    # ── GPSB CRS (ucode-pcode mailbox, ccp_status, dfx_ctrl) ─────────────
    print("\n  [gpsb_infvnn_crs]")
    crs = die.base.punit_regs.punit_gpsb.gpsb_infvnn_crs
    try:
        s = crs.ccp_status["fid_0"]
        dump_reg(crs, "ccp_status[fid_0].resolved_cores_state",   s.resolved_cores_state)
        dump_reg(crs, "ccp_status[fid_0].resolved_cores_sub_state", s.resolved_cores_sub_state)
        dump_reg(crs, "ccp_status[fid_0].lp_at_c0",               s.lp_at_c0)
    except Exception as e:
        print(f"    ccp_status: ERR {e}")

    try:
        dfx = crs.dfx_ctrl_unprotected
        dump_reg(crs, "dfx_ctrl.core_cstate_limit",   dfx.core_cstate_limit)
    except Exception as e:
        print(f"    dfx_ctrl: ERR {e}")

    # ── PMSB PCU (ccf_wp_status, ring_distress, acp_perf_limit) ──────────
    print("\n  [punit_pmsb.pmsb_pcu]")
    try:
        pmsb = die.base.punit_regs.punit_pmsb.pmsb_pcu
        dump_reg(pmsb, "ccf_wp_status.ratio",                 pmsb.ccf_wp_status.ratio)
        dump_reg(pmsb, "ccf_wp_status (raw)",                 pmsb.ccf_wp_status)
        dump_reg(pmsb, "ring_distress_status.ia_distress",    pmsb.ring_distress_status.ia_distress)
        dump_reg(pmsb, "ring_distress_status.ia_distress_invalid", pmsb.ring_distress_status.ia_distress_invalid)
        dump_reg(pmsb, "ring_distress_status.snoop_level",    pmsb.ring_distress_status.snoop_level)
        dump_reg(pmsb, "acp_perf_limit[fid_0] (raw)",         pmsb.acp_perf_limit["fid_0"])
    except Exception as e:
        print(f"    pmsb_pcu: ERR {e}")

    # ── TPMI UFS ──────────────────────────────────────────────────────────
    print("\n  [tpmi UFS]")
    try:
        tpmi = die.base.tpmi
        dump_reg(tpmi, "ufs_control (raw)",            tpmi.ufs_control)
        dump_reg(tpmi, "ufs_control.max_ratio",        tpmi.ufs_control.max_ratio)
        dump_reg(tpmi, "ufs_control.min_ratio",        tpmi.ufs_control.min_ratio)
        dump_reg(tpmi, "ufs_control.ufs_throttle_mode",tpmi.ufs_control.ufs_throttle_mode)
        dump_reg(tpmi, "ufs_status (raw)",             tpmi.ufs_status)
        dump_reg(tpmi, "ufs_status.current_ratio",     tpmi.ufs_status.current_ratio)
    except Exception as e:
        print(f"    tpmi UFS: ERR {e}")

    # ── TPMI PLR mailbox ──────────────────────────────────────────────────
    print("\n  [tpmi PLR mailbox]")
    try:
        dump_reg(tpmi, "plr_mailbox_interface",        tpmi.plr_mailbox_interface)
        dump_reg(tpmi, "plr_mailbox_data",             tpmi.plr_mailbox_data)
    except Exception as e:
        print(f"    plr_mailbox: ERR {e}")

    # ── GPSB IO regs (additional punit state) ────────────────────────────
    print("\n  [gpsb_infvnn_io_regs]")
    try:
        io = die.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs
        io_regs = list(io.registers)
        print(f"    Available io registers: {len(io_regs)}")
        # Sample the first 15 that sound PM-related
        pm_keywords = ['ratio', 'freq', 'gv', 'cstate', 'pstate', 'acp', 'rapl', 'pl1', 'pl2', 'power', 'pkg']
        for r in io_regs:
            if any(k in r.lower() for k in pm_keywords):
                try:
                    v = getattr(io, r)
                    dump_reg(io, r, v)
                except:
                    pass
    except Exception as e:
        print(f"    gpsb_infvnn_io_regs: ERR {e}")

    # ── Fuses (C-state limits) ────────────────────────────────────────────
    print("\n  [fuses]")
    try:
        fuses = die.base.punit_regs.fuses
        fuse_regs = list(fuses.registers)
        pm_keys = ['cstate', 'ratio', 'limit', 'freq', 'pstate', 'gv']
        for r in fuse_regs:
            if any(k in r.lower() for k in pm_keys):
                try:
                    dump_reg(fuses, r, getattr(fuses, r))
                except:
                    pass
    except Exception as e:
        print(f"    fuses: ERR {e}")

print("=" * 70)
print("NWP Simics CBB PCUDATA DUMP")
print("=" * 70)
for cbb in ["cbb0", "cbb1"]:
    dump_cbb(cbb)

print("\n" + "=" * 70)
print("Done.")

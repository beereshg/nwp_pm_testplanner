#!/usr/bin/python3

"""
tpmi_verify_cbb.py

HSD: 16030715615 - [PSS] TPMI register verification - CBB

Verifies TPMI (Topology Aware PM Interface) registers on the CBB (Compute Building Block) die.
Checks that key CBB-side TPMI registers are accessible and contain valid values after BIOS POST.

BIOS knobs required:
  - ProcessorHWPMEnable = 1   (Hardware P-States / HWP)
  - See setup_bios_knobs.csh for IFWI preparation steps

Namednodes path (CBB TPMI):
  sv.socket0.cbbs.base.punit.ptpcfsms.ptpcfsms.*
  sv.socketX.cbb<N>.base.punit.ptpcfsms.ptpcfsms.*  (per-CBB iteration)

Emulation: HSLE IMH2 M7 (MCP ICI) -- run via tpmi_cbb_run.csh
Post-Si:   import and call main() from PythonSV session
"""

import sys
import namednodes
import svtools.common.baseaccess as access

base = access.getglobalbase()
sv   = namednodes.sv.get_manager(['socket'])
sv.get_all(stop_on_error=True)

_ENV       = access.getaccess()
IS_SIMICS  = (_ENV == 'simics')
IS_SVOS    = (_ENV == 'svos')
IS_POST_SI = not IS_SIMICS

print(f"PM_INFO :: Detected access environment: '{_ENV}'  "
      f"({'emulation' if IS_SIMICS else 'post-silicon'})")

try:
    import cli  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    cli = None

if IS_SIMICS and cli is not None:
    try:
        cli.run_command("emu.engine.wait-for-cycle -relative 1000")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(node, label, pass_list, fail_list, expected=None):
    """
    Read a namednodes leaf. Append (label, value) to pass_list or fail_list.
    If expected is provided, fail if the value != expected.
    Returns the value on success, None on failure.
    """
    try:
        val = node.read()
        if expected is not None and int(val) != expected:
            print(f"PM_INFO :: FAIL  {label} = 0x{int(val):X}  (expected 0x{expected:X})")
            fail_list.append(label)
        else:
            print(f"PM_INFO :: OK    {label} = 0x{int(val):X}")
            pass_list.append(label)
        return val
    except Exception as exc:
        print(f"PM_INFO :: ERR   {label} -- {exc}")
        fail_list.append(label)
        return None


def _bios_cpl_check(skt):
    """Print and return CPL status; warn if not complete."""
    try:
        cpl = skt.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg
        c1 = cpl.rst_cpl1.read()
        c2 = cpl.rst_cpl2.read()
        c3 = cpl.rst_cpl3.read()
        c4 = cpl.rst_cpl4.read()
        print(f"PM_INFO :: BIOS CPL: 1={c1}  2={c2}  3={c3}  4={c4}")
        if not (c3 and c4):
            print("PM_INFO :: WARNING: BIOS CPL3/CPL4 incomplete -- TPMI values may be unreliable")
            return False
        return True
    except Exception as exc:
        print(f"PM_INFO :: BIOS CPL: not readable ({exc})")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    passed = []
    failed = []

    print("=" * 70)
    print("PM_INFO :: TPMI Register Verification - CBB  (HSD 16030715615)")
    print("=" * 70)

    for skt in sv.sockets:
        skt_num = skt.target_info['socket_num']
        print(f"\nPM_INFO :: ===== Socket {skt_num} =====")

        _bios_cpl_check(skt)

        # ---- Iterate over CBBs (compute dies) ----
        try:
            cbbs = list(skt.cbbs)
        except Exception as exc:
            print(f"PM_INFO :: ERR   Could not enumerate CBBs: {exc}")
            failed.append(f"skt{skt_num}.cbbs.enumerate")
            continue

        for cbb in cbbs:
            cbb_inst = cbb.target_info.get('instance', '?')
            print(f"\nPM_INFO :: -- CBB {cbb_inst} --")

            # ---- TPMI: HWP Capability (lowest / highest performance) ----
            print("PM_INFO :: [HWP Capability]")
            tpmi = None
            for tpmi_path in [
                lambda: cbb.base.punit.ptpcfsms.ptpcfsms,
                lambda: cbb.punit.ptpcfsms.ptpcfsms,
            ]:
                try:
                    tpmi = tpmi_path()
                    break
                except Exception:
                    pass

            if tpmi is None:
                print(f"PM_INFO :: ERR   CBB{cbb_inst}: TPMI path not found "
                      f"(tried cbb.base.punit.ptpcfsms / cbb.punit.ptpcfsms)")
                failed.append(f"skt{skt_num}.cbb{cbb_inst}.tpmi_path")
                continue

            cap_key = f"skt{skt_num}.cbb{cbb_inst}.opc_hwp_capability"
            try:
                cap = tpmi.opc_hwp_capability
                lo  = cap.lowest_performance.read()
                hi  = cap.highest_performance.read()
                guar= cap.guaranteed_performance.read()
                eff = cap.most_efficient_performance.read()
                print(f"PM_INFO :: OK    opc_hwp_capability.lowest      = 0x{int(lo):02X}")
                print(f"PM_INFO :: OK    opc_hwp_capability.highest     = 0x{int(hi):02X}")
                print(f"PM_INFO :: OK    opc_hwp_capability.guaranteed  = 0x{int(guar):02X}")
                print(f"PM_INFO :: OK    opc_hwp_capability.eff         = 0x{int(eff):02X}")
                # Sanity: highest >= guaranteed >= lowest, all > 0
                if int(hi) > 0 and int(lo) > 0 and int(hi) >= int(guar) >= int(lo):
                    print(f"PM_INFO :: OK    {cap_key} range check PASS")
                    passed.append(cap_key)
                else:
                    print(f"PM_INFO :: FAIL  {cap_key} range check (lo=0x{int(lo):X} guar=0x{int(guar):X} hi=0x{int(hi):X})")
                    failed.append(cap_key)
            except Exception as exc:
                print(f"PM_INFO :: ERR   {cap_key}: {exc}")
                failed.append(cap_key)

            # ---- TPMI: HWP Controls ----
            print("PM_INFO :: [HWP Controls]")
            for field_name in ['min', 'max', 'minimum_performance', 'maximum_performance']:
                key = f"skt{skt_num}.cbb{cbb_inst}.opc_hwp_controls.{field_name}"
                try:
                    val = getattr(tpmi.opc_hwp_controls, field_name).read()
                    print(f"PM_INFO :: OK    opc_hwp_controls.{field_name} = 0x{int(val):X}")
                    passed.append(key)
                except Exception as exc:
                    print(f"PM_INFO :: ERR   {key}: {exc}")
                    failed.append(key)

            # ---- TPMI: EPB (Energy Performance Bias) ----
            print("PM_INFO :: [Energy Performance Bias]")
            key = f"skt{skt_num}.cbb{cbb_inst}.opc_epb"
            try:
                epb = tpmi.opc_epb.read()
                print(f"PM_INFO :: OK    opc_epb = 0x{int(epb):X}  "
                      f"(0=max-performance  15=max-energy-saving)")
                passed.append(key)
            except Exception as exc:
                print(f"PM_INFO :: ERR   {key}: {exc}")
                failed.append(key)

            # ---- TPMI: HWP Request Package ----
            print("PM_INFO :: [HWP Request Package]")
            for field_name in ['minimum_performance', 'maximum_performance',
                               'desired_performance', 'energy_performance_preference']:
                key = f"skt{skt_num}.cbb{cbb_inst}.opc_hwp_request_pkg.{field_name}"
                try:
                    val = getattr(tpmi.opc_hwp_request_pkg, field_name).read()
                    print(f"PM_INFO :: OK    opc_hwp_request_pkg.{field_name} = 0x{int(val):X}")
                    passed.append(key)
                except Exception as exc:
                    print(f"PM_INFO :: ERR   {key}: {exc}")
                    failed.append(key)

            # ---- Per-core HWP requests (first core only to keep output concise) ----
            print("PM_INFO :: [Per-core HWP Request - core 0 sample]")
            try:
                core0 = list(cbb.base.modules.cores)[0]
                c_inst = core0.target_info.get('instance', 0)
                for field_name in ['minimum_performance', 'maximum_performance']:
                    key = f"skt{skt_num}.cbb{cbb_inst}.core{c_inst}.opc_hwp_request.{field_name}"
                    try:
                        val = getattr(tpmi.opc_hwp_request, field_name).read()
                        print(f"PM_INFO :: OK    core{c_inst} opc_hwp_request.{field_name} = 0x{int(val):X}")
                        passed.append(key)
                    except Exception as exc:
                        print(f"PM_INFO :: ERR   {key}: {exc}")
                        failed.append(key)
            except Exception as exc:
                print(f"PM_INFO :: INFO  Per-core iteration: {exc}")

    # ---- Summary ----
    print("\n" + "=" * 70)
    result = "PASS" if not failed else "FAIL"
    print(f"PM_INFO :: TPMI CBB Verification: {result}")
    print(f"PM_INFO ::   PASS: {len(passed)}  FAIL/ERR: {len(failed)}")
    if failed:
        for f in failed:
            print(f"PM_INFO ::   FAILED: {f}")
    print("=" * 70)

    if IS_SIMICS and cli is not None:
        try:
            cli.run_command(f"!echo '{result}' > test/results.log")
            cli.run_command("exit -f")
        except Exception:
            pass
        return


main()

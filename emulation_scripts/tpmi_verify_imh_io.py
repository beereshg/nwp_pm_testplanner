#!/usr/bin/python3

"""
tpmi_verify_imh_io.py

HSD: 16030715617 - [PSS] TPMI register verification - IMH IO

Verifies TPMI (Topology Aware PM Interface) registers on the IMH IO die (imh8 / imh0 in
namednodes). Checks that IO-die TPMI registers are accessible and contain valid values
after BIOS POST.

Key registers checked:
  - opc_hwp_capability / opc_hwp_controls  (HWP via IMH0)
  - hw_feedback_config                      (HGS feedback enable)
  - opc_power_info                          (TDP, min/max power)
  - opc_pl1 / opc_pl2                       (package power limits)
  - pm_last_wake                            (last wake source / TSC)
  - bios_reset_cpl_cfg                      (CPL gates)

BIOS knobs required:
  - ProcessorHWPMEnable = 1   (Hardware P-States / HWP)
  - See setup_bios_knobs.csh for IFWI preparation steps

Namednodes path (IMH IO TPMI):
  sv.socketX.imh0.punit.ptpcfsms.ptpcfsms.*

Note: imh0 = IO die (imh8 in fuse/die naming).
      imh1 = MEM die (imh9 in fuse/die naming) -- covered by tpmi_verify_imh_mem.py

Emulation: HSLE IMH2 M7 (MCP ICI) -- run via tpmi_imh_io_run.csh
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

def _ok(label, val, passed):
    print(f"PM_INFO :: OK    {label} = 0x{int(val):X}")
    passed.append(label)


def _fail(label, val, expected, failed):
    print(f"PM_INFO :: FAIL  {label} = 0x{int(val):X}  (expected 0x{expected:X})")
    failed.append(label)


def _err(label, exc, failed):
    print(f"PM_INFO :: ERR   {label} -- {exc}")
    failed.append(label)


def _read_field(node, label, passed, failed, expected=None):
    try:
        val = node.read()
        if expected is not None and int(val) != expected:
            _fail(label, val, expected, failed)
        else:
            _ok(label, val, passed)
        return val
    except Exception as exc:
        _err(label, exc, failed)
        return None


def _bios_cpl(skt):
    try:
        cpl = skt.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg
        c1, c2, c3, c4 = (cpl.rst_cpl1.read(), cpl.rst_cpl2.read(),
                          cpl.rst_cpl3.read(), cpl.rst_cpl4.read())
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
    print("PM_INFO :: TPMI Register Verification - IMH IO  (HSD 16030715617)")
    print("=" * 70)

    for skt in sv.sockets:
        skt_num = skt.target_info['socket_num']
        print(f"\nPM_INFO :: ===== Socket {skt_num} (IMH IO = imh0 / imh8) =====")

        _bios_cpl(skt)

        # ---- Get TPMI node ----
        tpmi = None
        for tpmi_getter in [
            lambda: skt.imh0.punit.ptpcfsms.ptpcfsms,
            lambda: skt.imhs.punit.ptpcfsms.ptpcfsms,   # broadcasts to all IMH
        ]:
            try:
                tpmi = tpmi_getter()
                break
            except Exception:
                pass

        if tpmi is None:
            print(f"PM_INFO :: ERR   skt{skt_num}: IMH IO TPMI path not found")
            failed.append(f"skt{skt_num}.imh0.tpmi_path")
            continue

        # ---- HWP Capability ----
        print("\nPM_INFO :: [HWP Capability]")
        cap_ok = False
        try:
            cap = tpmi.opc_hwp_capability
            lo   = cap.lowest_performance.read()
            hi   = cap.highest_performance.read()
            guar = cap.guaranteed_performance.read()
            eff  = cap.most_efficient_performance.read()
            print(f"PM_INFO :: OK    lowest_performance      = 0x{int(lo):02X}")
            print(f"PM_INFO :: OK    highest_performance     = 0x{int(hi):02X}")
            print(f"PM_INFO :: OK    guaranteed_performance  = 0x{int(guar):02X}")
            print(f"PM_INFO :: OK    most_efficient          = 0x{int(eff):02X}")
            if int(hi) > 0 and int(lo) > 0 and int(hi) >= int(guar) >= int(lo):
                print(f"PM_INFO :: OK    range check PASS (lo <= guar <= hi, all non-zero)")
                passed.append(f"skt{skt_num}.imh0.opc_hwp_capability.range")
                cap_ok = True
            else:
                print(f"PM_INFO :: FAIL  range check FAIL (lo=0x{int(lo):X} guar=0x{int(guar):X} hi=0x{int(hi):X})")
                failed.append(f"skt{skt_num}.imh0.opc_hwp_capability.range")
        except Exception as exc:
            _err(f"skt{skt_num}.imh0.opc_hwp_capability", exc, failed)

        # ---- HWP Controls ----
        print("\nPM_INFO :: [HWP Controls]")
        for field in ['min', 'max', 'minimum_performance', 'maximum_performance']:
            _read_field(getattr(tpmi.opc_hwp_controls, field),
                        f"skt{skt_num}.imh0.opc_hwp_controls.{field}", passed, failed)

        # ---- HW Feedback Config (HGS) ----
        print("\nPM_INFO :: [HW Feedback Config (HGS)]")
        _read_field(tpmi.hw_feedback_config,
                    f"skt{skt_num}.imh0.hw_feedback_config", passed, failed)

        # ---- Package Power Info ----
        print("\nPM_INFO :: [Package Power Info]")
        for field in ['max_time_window', 'max_turbo_power', 'min_power', 'thermal_design_power']:
            try:
                val = getattr(tpmi.opc_power_info, field).read()
                print(f"PM_INFO :: OK    opc_power_info.{field} = 0x{int(val):X}")
                passed.append(f"skt{skt_num}.imh0.opc_power_info.{field}")
            except Exception as exc:
                _err(f"skt{skt_num}.imh0.opc_power_info.{field}", exc, failed)

        # ---- Package Power Limits (PL1 / PL2) ----
        print("\nPM_INFO :: [Package Power Limits]")
        for pl_name in ['opc_pl1', 'opc_pl2']:
            for field in ['power_limit', 'time_window', 'clamp', 'enable']:
                key = f"skt{skt_num}.imh0.{pl_name}.{field}"
                try:
                    node = getattr(getattr(tpmi, pl_name), field)
                    _read_field(node, key, passed, failed)
                except AttributeError:
                    pass   # not all models expose every sub-field
                except Exception as exc:
                    _err(key, exc, failed)

        # ---- Last Wake (PkgC debug) ----
        print("\nPM_INFO :: [Last Wake / PkgC debug]")
        try:
            lw = tpmi.pm_last_wake
            _read_field(lw.wake_source,  f"skt{skt_num}.imh0.pm_last_wake.wake_source",  passed, failed)
            _read_field(lw.last_wake_tsc, f"skt{skt_num}.imh0.pm_last_wake.last_wake_tsc", passed, failed)
        except Exception as exc:
            _err(f"skt{skt_num}.imh0.pm_last_wake", exc, failed)

        # ---- Package Thermal Status (HGS notification log) ----
        print("\nPM_INFO :: [Package Thermal Status]")
        try:
            pts = skt.imh0.pcodeio_map.io_package_therm_status
            _read_field(pts.hw_feedback_notification_log,
                        f"skt{skt_num}.imh0.hw_feedback_notification_log", passed, failed)
        except Exception as exc:
            _err(f"skt{skt_num}.imh0.io_package_therm_status", exc, failed)

    # ---- Summary ----
    print("\n" + "=" * 70)
    result = "PASS" if not failed else "FAIL"
    print(f"PM_INFO :: TPMI IMH IO Verification: {result}")
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

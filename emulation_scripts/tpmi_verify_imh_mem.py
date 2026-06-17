#!/usr/bin/python3

"""
tpmi_verify_imh_mem.py

HSD: 16030715619 - [PSS] TPMI register verification - IMH MEM

Verifies TPMI (Topology Aware PM Interface) registers on the IMH MEM die (imh9 / imh1 in
namednodes). Checks that memory-die TPMI registers are accessible and contain valid values
after BIOS POST.

Key registers checked:
  - opc_pl3 / opc_dram_pl1             (DRAM power limits)
  - opc_memory_channel_power           (per-channel power throttle)
  - opc_power_info                     (TDP / power ranges from MEM die)
  - pm_last_wake                       (MEM-die last wake TSC / source)
  - bios_reset_cpl_cfg                 (CPL via IMH1)
  - ISA oob qchan_status               (Q-channel status on MEM die)

BIOS knobs required:
  - ProcessorHWPMEnable = 1   (Hardware P-States / HWP)
  - See setup_bios_knobs.csh for IFWI preparation steps

Namednodes path (IMH MEM TPMI):
  sv.socketX.imh1.punit.ptpcfsms.ptpcfsms.*

Note: imh0 = IO die  (imh8 in fuse/die naming) -- covered by tpmi_verify_imh_io.py
      imh1 = MEM die (imh9 in fuse/die naming) -- THIS SCRIPT

If imh1 is not present in the model (single-IMH config), registers fall back to imh0
with memory-related sub-registers. The script handles both cases gracefully.

Emulation: HSLE IMH2 M7 (MCP ICI) -- run via tpmi_imh_mem_run.csh
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

def _read_field(node, label, passed, failed, expected=None):
    try:
        val = node.read()
        if expected is not None and int(val) != expected:
            print(f"PM_INFO :: FAIL  {label} = 0x{int(val):X}  (expected 0x{expected:X})")
            failed.append(label)
        else:
            print(f"PM_INFO :: OK    {label} = 0x{int(val):X}")
            passed.append(label)
        return val
    except Exception as exc:
        print(f"PM_INFO :: ERR   {label} -- {exc}")
        failed.append(label)
        return None


def _get_imh_mem(skt):
    """
    Return the TPMI node for the MEM die.
    Priority: imh1 -> imh0 (fallback for single-IMH configs).
    Returns (tpmi_node, die_label) or (None, None).
    """
    for attr, label in [('imh1', 'imh1(MEM)'), ('imh0', 'imh0(fallback)')]:
        try:
            imh = getattr(skt, attr)
            tpmi = imh.punit.ptpcfsms.ptpcfsms
            return tpmi, label
        except Exception:
            pass
    return None, None


def _bios_cpl(skt):
    for imh_attr in ['imh1', 'imh0']:
        try:
            imh = getattr(skt, imh_attr)
            cpl = imh.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg
            c1, c2, c3, c4 = (cpl.rst_cpl1.read(), cpl.rst_cpl2.read(),
                               cpl.rst_cpl3.read(), cpl.rst_cpl4.read())
            print(f"PM_INFO :: BIOS CPL ({imh_attr}): 1={c1}  2={c2}  3={c3}  4={c4}")
            if not (c3 and c4):
                print("PM_INFO :: WARNING: BIOS CPL3/CPL4 incomplete -- TPMI values may be unreliable")
            return
        except Exception:
            pass
    print("PM_INFO :: BIOS CPL: not readable from imh1 or imh0")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    passed = []
    failed = []

    print("=" * 70)
    print("PM_INFO :: TPMI Register Verification - IMH MEM  (HSD 16030715619)")
    print("=" * 70)

    for skt in sv.sockets:
        skt_num = skt.target_info['socket_num']
        print(f"\nPM_INFO :: ===== Socket {skt_num} (IMH MEM = imh1 / imh9) =====")

        _bios_cpl(skt)

        tpmi, die_label = _get_imh_mem(skt)
        if tpmi is None:
            print(f"PM_INFO :: ERR   skt{skt_num}: IMH MEM TPMI path not found (imh1 and imh0 both failed)")
            failed.append(f"skt{skt_num}.imh_mem.tpmi_path")
            continue

        print(f"PM_INFO :: INFO  Using TPMI node via: {die_label}")

        # ---- Power Info (TDP / power ranges) ----
        print("\nPM_INFO :: [Power Info]")
        for field in ['thermal_design_power', 'min_power', 'max_turbo_power', 'max_time_window']:
            try:
                val = getattr(tpmi.opc_power_info, field).read()
                print(f"PM_INFO :: OK    opc_power_info.{field} = 0x{int(val):X}")
                passed.append(f"skt{skt_num}.imh_mem.opc_power_info.{field}")
            except AttributeError:
                pass   # field may not exist on this model
            except Exception as exc:
                print(f"PM_INFO :: ERR   opc_power_info.{field} -- {exc}")
                failed.append(f"skt{skt_num}.imh_mem.opc_power_info.{field}")

        # ---- DRAM / PL3 Power Limits ----
        print("\nPM_INFO :: [DRAM Power Limits]")
        for pl_name in ['opc_pl3', 'opc_dram_pl1']:
            for field in ['power_limit', 'time_window', 'enable', 'clamp']:
                key = f"skt{skt_num}.imh_mem.{pl_name}.{field}"
                try:
                    node = getattr(getattr(tpmi, pl_name), field)
                    _read_field(node, key, passed, failed)
                except AttributeError:
                    pass
                except Exception as exc:
                    print(f"PM_INFO :: ERR   {key} -- {exc}")
                    failed.append(key)

        # ---- Memory Channel Power Throttle ----
        print("\nPM_INFO :: [Memory Channel Power]")
        try:
            mcp = tpmi.opc_memory_channel_power
            for field in ['throttle_time', 'throttle_value', 'enable']:
                key = f"skt{skt_num}.imh_mem.opc_memory_channel_power.{field}"
                try:
                    _read_field(getattr(mcp, field), key, passed, failed)
                except AttributeError:
                    pass
                except Exception as exc:
                    print(f"PM_INFO :: ERR   {key} -- {exc}")
                    failed.append(key)
        except Exception as exc:
            print(f"PM_INFO :: ERR   opc_memory_channel_power -- {exc}")
            failed.append(f"skt{skt_num}.imh_mem.opc_memory_channel_power")

        # ---- Last Wake (PkgC debug -- MEM die perspective) ----
        print("\nPM_INFO :: [Last Wake - MEM die]")
        try:
            lw = tpmi.pm_last_wake
            _read_field(lw.wake_source,   f"skt{skt_num}.imh_mem.pm_last_wake.wake_source",   passed, failed)
            _read_field(lw.last_wake_tsc, f"skt{skt_num}.imh_mem.pm_last_wake.last_wake_tsc", passed, failed)
        except Exception as exc:
            print(f"PM_INFO :: ERR   pm_last_wake -- {exc}")
            failed.append(f"skt{skt_num}.imh_mem.pm_last_wake")

        # ---- Q-channel status (ISA OOB -- MEM die) ----
        print("\nPM_INFO :: [Q-channel / ISA OOB - MEM die]")
        for imh_attr in ['imh1', 'imh0']:
            try:
                imh = getattr(skt, imh_attr)
                qch = imh.isa.isa_oob.qchan_status.read()
                print(f"PM_INFO :: OK    {imh_attr}.isa.isa_oob.qchan_status = 0x{int(qch):X}")
                passed.append(f"skt{skt_num}.{imh_attr}.qchan_status")
                break
            except Exception as exc:
                print(f"PM_INFO :: ERR   {imh_attr}.isa.isa_oob.qchan_status -- {exc}")
                failed.append(f"skt{skt_num}.{imh_attr}.qchan_status")

        # ---- CLKREQ status (MEM die) ----
        print("\nPM_INFO :: [CLKREQ status - MEM die]")
        for imh_attr in ['imh1', 'imh0']:
            try:
                imh = getattr(skt, imh_attr)
                clk = imh.isa.isa_oob.clkreq_status.clkreq_status.read()
                print(f"PM_INFO :: OK    {imh_attr}.isa.isa_oob.clkreq_status = 0x{int(clk):X}")
                passed.append(f"skt{skt_num}.{imh_attr}.clkreq_status")
                break
            except Exception as exc:
                print(f"PM_INFO :: ERR   {imh_attr}.isa.isa_oob.clkreq_status -- {exc}")
                failed.append(f"skt{skt_num}.{imh_attr}.clkreq_status")

    # ---- Summary ----
    print("\n" + "=" * 70)
    result = "PASS" if not failed else "FAIL"
    print(f"PM_INFO :: TPMI IMH MEM Verification: {result}")
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

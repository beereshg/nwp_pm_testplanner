#!/usr/bin/env python3
"""
test_cpuid6_hgs.py

Test: HGS CPUID.6 Field Validation
====================================
Verify CPUID.6.EAX[19] (HW_FEEDBACK) and the associated EDX fields.

Expected values
---------------
  EAX[19]   : 1  – HW Feedback (HGS) is supported
  EDX[7:0]  : 0x01 for Server  (performance capability only)
               0x03 for Client  (performance + energy-efficiency)
  EDX[11:8] : 0x00 – HGS information table is one 4 K page

Usage
-----
  %run test_cpuid6_hgs.py               (IPython / PythonSV shell)
    python test_cpuid6_hgs.py [--platform {server,client,auto}]
"""

import sys
import argparse
import re
import os

import namednodes
import svtools.common.baseaccess as access

base = access.getglobalbase()
sv   = namednodes.sv.get_manager(['socket'])
sv.get_all(stop_on_error=True)
_ENV = access.getaccess()
ACCESS_METHOD = str(_ENV).lower()
IS_SIMICS = ACCESS_METHOD in ("simics", "simicsmailbox", "stub")


def _is_cfg_emulation():
    """PSS-style emulation detection for HSLE/VP environments."""
    try:
        cfg = getattr(access, "CFG", None)
        if cfg is None:
            return False
        dmr_cfg = getattr(cfg, "diamondrapids", None)
        if dmr_cfg is None:
            return False
        return hasattr(dmr_cfg, "emulation")
    except Exception:
        return False


IS_EMULATION = IS_SIMICS or _is_cfg_emulation()
IS_XOS_MODEL = ("xos" in ACCESS_METHOD)

try:
    import diamondrapids.svos.simics_magic_breakpoint as _smb
except ModuleNotFoundError:
    _smb = None

try:
    import cli  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    cli = None

# ── Constants ─────────────────────────────────────────────────────────────────
CPUID_LEAF_6        = 6
HW_FEEDBACK_BIT     = 19           # EAX[19]
EDX_CAP_MASK        = 0x0FF        # EDX[7:0]  – capability bitmap
EDX_TABLE_MASK      = 0xF00        # EDX[11:8] – table size (pages − 1)
EDX_TABLE_SHIFT     = 8

EXPECTED_CAP_SERVER = 0x01         # performance capability only
EXPECTED_CAP_CLIENT = 0x03         # performance + energy-efficiency
EXPECTED_TABLE_SIZE = 0x00         # one 4 K page

# Default platform – override via --platform when running as a standalone script
PLATFORM = "auto"
VERBOSE_CORE_PATHS = False
EMU_WAIT_CYCLES = 1000
XOS_TRANSITION_MODE = "auto"


def _maybe_xos_transition(mode=XOS_TRANSITION_MODE):
    """PSS-style XOS transition hook using xpressos-switch when available."""
    mode = str(mode).lower()
    if mode not in ("auto", "on", "off"):
        mode = "auto"
    if mode == "off":
        return

    should_try = (mode == "on") or IS_XOS_MODEL or os.path.exists("/usr/bin/xpressos-switch")
    if not should_try:
        return

    if _smb is None:
        if mode == "on":
            print("PM_INFO :: XOS transition requested but simics_magic_breakpoint is unavailable")
        return

    try:
        rc = _smb.xos_driver_transition()
        print(f"PM_INFO :: XOS transition attempted (rc={rc})")
    except Exception as exc:
        if mode == "on":
            print(f"PM_INFO :: XOS transition failed: {exc}")


def _emu_wait(cycles=EMU_WAIT_CYCLES):
    """Best-effort wait for emulation to settle; no-op on post-si."""
    if not IS_EMULATION or cli is None:
        return
    try:
        cli.run_command(f"emu.engine.wait-for-cycle -relative {int(cycles)}")
    except Exception:
        pass


def _get_core_thread(core):
    """Return a logical processor object for CPUID access from a core object."""
    threads = getattr(core, "threads", None)
    if threads is not None:
        try:
            if len(threads) > 0:
                return threads[0]
        except Exception:
            pass

    thread0 = getattr(core, "thread0", None)
    if thread0 is not None:
        return thread0

    return None


def _format_core_label(skt_num, core, lp_idx):
    """Return a unique short label like S0M124C1 (fallback S0LP37)."""
    path = str(getattr(core, "path", ""))
    m = re.search(r"module(\d+)\.core(\d+)", path)
    if m:
        return f"S{skt_num}M{m.group(1)}C{m.group(2)}"
    return f"S{skt_num}LP{lp_idx}"


def _get_global_threads():
    """Return logical processor objects from common PythonSV globals."""
    if "cpu" in globals() and hasattr(cpu, "threads"):
        try:
            return list(cpu.threads)
        except Exception:
            pass

    if "itp" in globals() and hasattr(itp, "threads"):
        try:
            return list(itp.threads)
        except Exception:
            pass

    return []


def _cpuid6_from_thread(thread_obj):
    """Execute CPUID leaf 0x6 on a thread object using common APIs."""
    def _retry_halted(callable_cpuid):
        # In some ITP environments, CPUID requires a halted thread.
        controller = globals().get("itp", None)
        halt = getattr(controller, "halt", None)
        go = getattr(controller, "go", None)

        if callable(halt) and callable(go):
            halted = False
            try:
                halt()
                halted = True
                return callable_cpuid()
            finally:
                if halted:
                    go()

        thread_halt = getattr(thread_obj, "halt", None)
        thread_go = getattr(thread_obj, "go", None)
        if callable(thread_halt) and callable(thread_go):
            halted = False
            try:
                thread_halt()
                halted = True
                return callable_cpuid()
            finally:
                if halted:
                    thread_go()

        raise RuntimeError("Thread_Not_Halted and no halt/go control available")

    if hasattr(thread_obj, "cpuid"):
        try:
            res = thread_obj.cpuid(0x6)
            if isinstance(res, dict):
                return {
                    "eax": int(res["eax"]),
                    "ebx": int(res["ebx"]),
                    "ecx": int(res["ecx"]),
                    "edx": int(res["edx"]),
                }
        except TypeError:
            pass

        try:
            res = thread_obj.cpuid(0x6, 0x0)
            if isinstance(res, dict):
                return {
                    "eax": int(res["eax"]),
                    "ebx": int(res["ebx"]),
                    "ecx": int(res["ecx"]),
                    "edx": int(res["edx"]),
                }
        except TypeError:
            pass
        except Exception as exc:
            if "Thread_Not_Halted" in str(exc):
                res = _retry_halted(lambda: thread_obj.cpuid(0x6, 0x0))
                if isinstance(res, dict):
                    return {
                        "eax": int(res["eax"]),
                        "ebx": int(res["ebx"]),
                        "ecx": int(res["ecx"]),
                        "edx": int(res["edx"]),
                    }
            raise

    if hasattr(thread_obj, "exec_cpuid"):
        res = thread_obj.exec_cpuid(eax=0x6, ecx=0x0)
        return {
            "eax": int(res["eax"]),
            "ebx": int(res["ebx"]),
            "ecx": int(res["ecx"]),
            "edx": int(res["edx"]),
        }

    if hasattr(thread_obj, "cpuid_eax"):
        return {
            "eax": int(thread_obj.cpuid_eax(0x6, 0x0)),
            "ebx": int(thread_obj.cpuid_ebx(0x6, 0x0)) if hasattr(thread_obj, "cpuid_ebx") else 0,
            "ecx": int(thread_obj.cpuid_ecx(0x6, 0x0)) if hasattr(thread_obj, "cpuid_ecx") else 0,
            "edx": int(thread_obj.cpuid_edx(0x6, 0x0)) if hasattr(thread_obj, "cpuid_edx") else 0,
        }

    raise RuntimeError("No supported CPUID API found on thread object")


def _cpuid6_from_did(did):
    """Read CPUID.6 through baseaccess DID mapping."""
    res = base.cpuid(eax=CPUID_LEAF_6, ecx=0, did=did)
    return {
        "eax": int(res["eax"]),
        "ebx": int(res.get("ebx", 0)),
        "ecx": int(res.get("ecx", 0)),
        "edx": int(res["edx"]),
    }


def _cpuid6_from_thread_or_did(thread_obj):
    """Try thread CPUID first, then DID fallback if available."""
    try:
        return _cpuid6_from_thread(thread_obj), None
    except Exception as thread_exc:
        tinfo = getattr(thread_obj, "target_info", {})
        did = tinfo.get("did") if hasattr(tinfo, "get") else None
        if did is not None:
            try:
                return _cpuid6_from_did(did), None
            except Exception:
                pass
        return None, str(thread_exc)


def _read_cpuid6_for_core(core, preferred_lp_idx=None):
    """Read CPUID.6 for a given core using hgs_read priority and fallbacks."""
    # In emulation, DID-based CPUID is generally the most reliable path.
    if IS_EMULATION:
        try:
            did = core.target_info['did']
            return _cpuid6_from_did(did), None
        except Exception:
            pass

    t = _get_core_thread(core)
    if t is not None:
        cpuid6, err = _cpuid6_from_thread_or_did(t)
        if cpuid6 is not None:
            return cpuid6, None

    global_threads = _get_global_threads()
    if preferred_lp_idx is not None and 0 <= preferred_lp_idx < len(global_threads):
        cpuid6, err = _cpuid6_from_thread_or_did(global_threads[preferred_lp_idx])
        if cpuid6 is not None:
            return cpuid6, None

    for t in global_threads:
        cpuid6, err = _cpuid6_from_thread_or_did(t)
        if cpuid6 is not None:
            return cpuid6, None

    # DID-based CPUID fallback for emulation paths.
    if IS_EMULATION:
        try:
            did = core.target_info['did']
            return _cpuid6_from_did(did), None
        except Exception as exc:
            return None, str(exc)

    return None, "No CPUID-capable thread found for core in current environment"


def _read_cpuid6_for_socket(skt, core_list):
    """Read CPUID.6 for a socket using same order as hgs_read.py."""
    if IS_EMULATION and len(core_list) > 0:
        try:
            did = core_list[0].target_info['did']
            return _cpuid6_from_did(did), None
        except Exception:
            pass

    try:
        res = base.cpuid(eax=CPUID_LEAF_6, ecx=0)
        return {
            "eax": int(res["eax"]),
            "ebx": int(res.get("ebx", 0)),
            "ecx": int(res.get("ecx", 0)),
            "edx": int(res["edx"]),
        }, None
    except Exception:
        pass

    t = getattr(skt, 'thread0', None)
    if t is not None and hasattr(t, 'cpuid'):
        cpuid6, err = _cpuid6_from_thread_or_did(t)
        if cpuid6 is not None:
            return cpuid6, None

    last_err = "No CPUID-capable thread found"
    for core in core_list:
        cpuid6, err = _read_cpuid6_for_core(core)
        if cpuid6 is not None:
            return cpuid6, None
        if err:
            last_err = err

    for t in _get_global_threads():
        cpuid6, err = _cpuid6_from_thread_or_did(t)
        if cpuid6 is not None:
            return cpuid6, None
        if err:
            last_err = err

    return None, last_err


def main(
    platform: str = PLATFORM,
    emu_wait_cycles: int = EMU_WAIT_CYCLES,
    xos_transition: str = XOS_TRANSITION_MODE,
) -> int:
    """
    Execute the HGS CPUID.6 validation across all cores.

    Returns 0 on overall PASS, 1 on any FAIL.
    """
    platform = platform.lower()
    expected_cap = None
    if platform == "server":
        expected_cap = EXPECTED_CAP_SERVER
    elif platform == "client":
        expected_cap = EXPECTED_CAP_CLIENT

    print("=" * 80)
    print("HGS CPUID.6 Field Validation")
    print("=" * 80)
    print(f"Access method             : {ACCESS_METHOD}")
    print(f"Emulation mode            : {IS_EMULATION}")
    print(f"XOS model detected        : {IS_XOS_MODEL}")
    print(f"Platform                  : {platform}")
    print(f"Expected EAX[19]          : 1")
    if expected_cap is None:
        print("Expected EDX[7:0]         : auto (first observed value, must be consistent)")
    else:
        print(f"Expected EDX[7:0]         : 0x{expected_cap:02X}")
    print(f"Expected EDX[11:8]        : 0x{EXPECTED_TABLE_SIZE:02X}\n")

    results = []
    _maybe_xos_transition(mode=xos_transition)
    _emu_wait(cycles=emu_wait_cycles)

    for skt in sv.sockets:
        print("skt value is: ", skt)
        coreList = list(skt.cbbs.computes.modules.cores)
        if VERBOSE_CORE_PATHS:
            for core in coreList:
                print("Core value is: ", core.path)
        else:
            print(f"Core count                : {len(coreList)}")

        sktNum = skt.target_info['socket_num']
        print("socket number is: ", sktNum)

        skt_cpuid6, skt_err = _read_cpuid6_for_socket(skt, coreList)

        if skt_cpuid6 is None:
            print(f"socket {sktNum}: unable to read CPUID.6 ({skt_err}), skipping socket")
            continue

        hwp_cpuid = (skt_cpuid6['eax'] >> 7) & 1
        if hwp_cpuid != 1:
            print(f"socket {sktNum}: HWP CPUID bit7 is 0")

        for lp_idx, core in enumerate(coreList):
            core_label = _format_core_label(sktNum, core, lp_idx)
            cpuid6, core_err = _read_cpuid6_for_core(core, preferred_lp_idx=lp_idx)
            if cpuid6 is None:
                results.append({
                    "label":   core_label,
                    "eax":     0,
                    "ebx":     0,
                    "ecx":     0,
                    "edx":     0,
                    "hw_fb":   False,
                    "cap":     0,
                    "exp_cap": expected_cap,
                    "cap_ok":  False,
                    "tbl":     0,
                    "tbl_ok":  False,
                    "status":  "FAIL",
                    "error":   core_err,
                })
                continue

            eax = int(cpuid6['eax'])
            ebx = int(cpuid6.get('ebx', 0))
            ecx = int(cpuid6.get('ecx', 0))
            edx = int(cpuid6['edx'])

            hw_fb  = bool((eax >> HW_FEEDBACK_BIT) & 1)
            cap    = edx & EDX_CAP_MASK
            if expected_cap is None:
                expected_cap = cap
                print(f"Detected EDX[7:0] baseline : 0x{expected_cap:02X}")
            cap_ok = (cap == expected_cap)
            tbl    = (edx & EDX_TABLE_MASK) >> EDX_TABLE_SHIFT
            tbl_ok = (tbl == EXPECTED_TABLE_SIZE)

            results.append({
                "label":   core_label,
                "eax":     eax,
                "ebx":     ebx,
                "ecx":     ecx,
                "edx":     edx,
                "hw_fb":   hw_fb,
                "cap":     cap,
                "exp_cap": expected_cap,
                "cap_ok":  cap_ok,
                "tbl":     tbl,
                "tbl_ok":  tbl_ok,
                "status":  "PASS" if (hw_fb and cap_ok and tbl_ok) else "FAIL",
            })

    # ── Per-thread detail table ────────────────────────────────────────────────
    hdr = (
        f"{'Core':>12}  {'EAX':>10}  {'EBX':>10}  {'ECX':>10}  {'EDX':>10}  "
        f"{'EAX[19]':>7}  {'EDX[7:0]':>22}  {'EDX[11:8]':>22}  Status"
    )
    print(hdr)
    print("-" * len(hdr))

    for r in results:
        hw_str  = "1 PASS" if r["hw_fb"]  else "0 FAIL"
        cap_str = f"0x{r['cap']:02X} (exp 0x{r['exp_cap']:02X}) {'PASS' if r['cap_ok'] else 'FAIL'}"
        tbl_str = f"0x{r['tbl']:02X} (exp 0x{EXPECTED_TABLE_SIZE:02X}) {'PASS' if r['tbl_ok'] else 'FAIL'}"

        print(
            f"{r['label']:>12}  0x{r['eax']:08X}  0x{r['ebx']:08X}  0x{r['ecx']:08X}  0x{r['edx']:08X}  "
            f"{hw_str:>7}  {cap_str:>22}  {tbl_str:>22}  {r['status']}"
        )

    # ── Summary ────────────────────────────────────────────────────────────────
    total  = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    if total == 0:
        failed = 1

    print()
    print("=" * 80)
    print(f"SUMMARY  Total={total}  PASS={passed}  FAIL={failed}")
    print("=" * 80)

    if failed:
        print("\nFailing cores:")
        for r in results:
            if r["status"] != "FAIL":
                continue
            reasons = []
            if r.get("error"):
                reasons.append(r["error"])
            if not r["hw_fb"]:
                reasons.append("EAX[19]=0 (HW_FEEDBACK not set)")
            if not r["cap_ok"]:
                reasons.append(f"EDX[7:0]=0x{r['cap']:02X} expected 0x{r['exp_cap']:02X}")
            if not r["tbl_ok"]:
                reasons.append(f"EDX[11:8]=0x{r['tbl']:02X} expected 0x{EXPECTED_TABLE_SIZE:02X}")
            print(f"  {r['label']}: {'; '.join(reasons)}")

    overall = "PASS" if (total > 0 and failed == 0) else "FAIL"
    print(f"\nTEST RESULT: {overall}\n")
    return 0 if overall == "PASS" else 1


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate HGS CPUID.6 fields on all sockets."
    )
    parser.add_argument(
        "--platform",
        choices=["server", "client", "auto"],
        default="auto",
        help="server=0x01, client=0x03, auto=use first observed value and check consistency. Default: auto",
    )
    parser.add_argument(
        "--emu-wait-cycles",
        type=int,
        default=EMU_WAIT_CYCLES,
        help="Simics-only startup wait cycles before CPUID reads. Ignored on post-si. Default: 1000",
    )
    parser.add_argument(
        "--xos-transition",
        choices=["auto", "on", "off"],
        default=XOS_TRANSITION_MODE,
        help="XOS driver transition control: auto=best-effort when XOS is detected, on=force, off=disable.",
    )
    args = parser.parse_args()
    main(
        platform=args.platform,
        emu_wait_cycles=args.emu_wait_cycles,
        xos_transition=args.xos_transition,
    )

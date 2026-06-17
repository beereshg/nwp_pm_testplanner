"""
discover_all_registers.py - Discover ALL available registers in NWP PM namednodes.
Queries live Simics session and dumps complete register lists from:
  - CBB0/CBB1 base.tpmi
  - CBB0 base.punit_regs.punit_pmsb.pmsb_pcu
  - IMH0 ptpcfsms.ptpcfsms
  - IMH0 ptpcfsms_pmsb.ptpcfsms_pmsb
  - IMH0 ptpcioregs.ptpcioregs
  - CBB0 compute0 GPSB path

Output: discover_results.json
"""
import socket, time, re, json, os

OUT = os.path.join(os.path.dirname(__file__), "discover_results.json")


def simics_cmd(s, cmd, wait=4):
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    s.settimeout(2)
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


def parse_list(text):
    """Extract Python list from Simics output that may contain log messages."""
    # Remove Simics log lines (lines containing spec-viol, info], etc.)
    clean = "\n".join(
        l for l in text.splitlines()
        if not re.search(r'spec-viol|info\]|running>|Traceback|\bError\b', l)
    )
    m = re.search(r'\[.*?\]', clean, re.DOTALL)
    if m:
        try:
            return eval(m.group(0))
        except Exception:
            pass
    # Fallback: extract quoted strings
    return re.findall(r"'([^']+)'", clean)


s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

results = {}

# CBB0 TPMI
print("Discovering CBB0 base.tpmi registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.cbb0.base.tpmi.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["cbb0_tpmi"] = {"path": "sv.socket0.cbb0.base.tpmi", "registers": parse_list(r)}
print(f"  cbb0.base.tpmi: {len(results['cbb0_tpmi']['registers'])} registers")

# CBB1 TPMI - same structure, just list count
print("Discovering CBB1 base.tpmi registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.cbb1.base.tpmi.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["cbb1_tpmi"] = {"path": "sv.socket0.cbb1.base.tpmi", "registers": parse_list(r)}
print(f"  cbb1.base.tpmi: {len(results['cbb1_tpmi']['registers'])} registers")

# CBB0 PMSB
print("Discovering CBB0 pmsb_pcu registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["cbb0_pmsb_pcu"] = {"path": "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu", "registers": parse_list(r)}
print(f"  cbb0 pmsb_pcu: {len(results['cbb0_pmsb_pcu']['registers'])} registers")

# IMH0 ptpcfsms
print("Discovering IMH0 ptpcfsms registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["imh0_ptpcfsms"] = {"path": "sv.socket0.imh0.punit.ptpcfsms.ptpcfsms", "registers": parse_list(r)}
print(f"  imh0 ptpcfsms: {len(results['imh0_ptpcfsms']['registers'])} registers")

# IMH0 ptpcfsms_pmsb
print("Discovering IMH0 ptpcfsms_pmsb registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["imh0_ptpcfsms_pmsb"] = {"path": "sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb", "registers": parse_list(r)}
print(f"  imh0 ptpcfsms_pmsb: {len(results['imh0_ptpcfsms_pmsb']['registers'])} registers")

# IMH0 ptpcioregs
print("Discovering IMH0 ptpcioregs registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["imh0_ptpcioregs"] = {"path": "sv.socket0.imh0.punit.ptpcioregs.ptpcioregs", "registers": parse_list(r)}
print(f"  imh0 ptpcioregs: {len(results['imh0_ptpcioregs']['registers'])} registers")

# CBB0 GPSB (pma0)
print("Discovering CBB0 compute0 pma0 gpsb registers...")
r = simics_cmd(s, "@print(sorted(list(sv.socket0.cbb0.compute0.getbypath('pma0').gpsb.registers)))", wait=6)
m = re.search(r'\[.*\]', r, re.DOTALL)
results["cbb0_gpsb_pma0"] = {"path": "sv.socket0.cbb0.compute0.getbypath('pma0').gpsb", "registers": parse_list(r)}
print(f"  cbb0 gpsb pma0: {len(results['cbb0_gpsb_pma0']['registers'])} registers")

s.close()

total = sum(len(v["registers"]) for v in results.values())
print(f"\nTotal discovered: {total} registers across {len(results)} paths")

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved to {OUT}")

# Print summary
for key, val in results.items():
    print(f"\n=== {val['path']} ({len(val['registers'])} regs) ===")
    for reg in val["registers"]:
        print(f"  {reg}")

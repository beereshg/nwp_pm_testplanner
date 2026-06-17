"""
Equivalent of sv.socket0.cbb0.pcudata.logregisters() for NWP Simics.
Dumps all readable punit registers for CBB0 and CBB1 to a file.
Output file: /tmp/pcudata_cbb0_203.txt
"""
import namednodes as n

OUT = "/tmp/pcudata_cbb0_203.txt"
lines = []

def log(s=""):
    lines.append(s)
    print(s)

def dump_component(comp, path, depth=0):
    indent = "  " * depth
    # Dump registers
    try:
        for reg in comp.registers:
            try:
                val = getattr(comp, reg)
                log(f"{indent}{path}.{reg} = {hex(int(val))}")
            except Exception as e:
                log(f"{indent}{path}.{reg} = ERR:{type(e).__name__}")
    except:
        pass
    # Recurse into sub-components
    try:
        for sub in comp.sub_component_names:
            try:
                sub_obj = getattr(comp, sub)
                dump_component(sub_obj, f"{path}.{sub}", depth+1)
            except:
                pass
    except:
        pass

for cbb_name in ["cbb0", "cbb1"]:
    die = getattr(n.sv.socket0, cbb_name)
    log(f"\n{'='*70}")
    log(f"sv.socket0.{cbb_name}.pcudata (punit_regs equivalent)")
    log(f"{'='*70}")
    try:
        dump_component(
            die.base.punit_regs,
            f"sv.socket0.{cbb_name}.base.punit_regs"
        )
    except Exception as e:
        log(f"ERROR: {e}")

# Write to file
with open(OUT, "w") as f:
    f.write("\n".join(lines))
print(f"\nWritten to {OUT} ({len(lines)} lines)")

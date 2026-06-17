"""
Wrapper script to run multiple pmax tests in a single CRT/emurun job.
Add or remove test script paths below as needed.
"""
import sys
import os
import importlib.util

# List your pmax test scripts here (full paths on NFS)
test_scripts = [
    "/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pmax/pmax_dfx_inject.py",
    # Add more test scripts below, e.g.:
    # "/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pmax/pmax_read.py",
    # "/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pmax/pmax_test2.py",
]

def run_script(script_path):
    """Load and execute a pythonsv test script."""
    script_name = os.path.basename(script_path).replace('.py', '')
    print(f"\n{'='*60}")
    print(f"Running: {script_path}")
    print(f"{'='*60}\n")

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If the script has a main() function, call it
    if hasattr(module, 'main'):
        module.main()

for script in test_scripts:
    if not os.path.exists(script):
        print(f"WARNING: Script not found: {script}")
        continue
    try:
        run_script(script)
    except Exception as e:
        print(f"ERROR running {script}: {e}")
        # Continue to next test even if one fails
        continue

print("\n" + "="*60)
print("All pmax tests completed.")
print("="*60)

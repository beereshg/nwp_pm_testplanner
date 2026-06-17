#!/usr/intel/bin/tcsh
# =============================================================================
# setup_bios_knobs.csh
#
# Prepares a modified IFWI binary with HWP enabled for TPMI PSS emulation runs.
#
# Required for HSD:
#   16030715615 - TPMI register verification - CBB
#   16030715617 - TPMI register verification - IMH IO
#   16030715619 - TPMI register verification - IMH MEM
#
# Why: BIOS knob ProcessorHWPMEnable=1 must be set before POST completes,
#      otherwise HWP TPMI registers are not initialized by firmware.
#
# Reference: https://wiki.ith.intel.com/spaces/PPA/pages/1774958664/Modifying+BIOS+knobs+with+XmlCli
#
# Usage:
#   1. Edit IFWI_SOURCE_DIR and IFWI_BASENAME below to match your release
#   2. Run: tcsh setup_bios_knobs.csh
#   3. Verify: ls -la /nfs/site/disks/ive_dmr_prednv_009/${USER}/bios_knob_hwp/
#
# After running this script, update the -io IFWI= path in your .csh run files
# to point to the directory created here.
# =============================================================================

# ---- EDIT THESE to match your release ----------------------------------------
# Source directory containing the base IFWI binaries
set IFWI_SOURCE_DIR = "/nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/26ww11.4_imh2_mcp_ici/ifwi"

# Exact filename of the HWP-enabled IFWI for socket 0 (ifwi1.bin)
# Look for a filename containing "HwpEn" or "hwp_en" in the release folder
set IFWI_S0_BASENAME = "OKSDCRB1_86B_2026.09.2.02_0032.D77_Simics_1-hsle_26ww11_4_1_PCIe_en_HwpEn.bin"

# Exact filename for socket 1 (ifwi2.bin)
set IFWI_S1_BASENAME = "OKSDCRB1_86B_2026.09.2.02_0032.D77_Simics_2.bin"

# Destination directory (your personal NFS area)
set DEST_DIR = "/nfs/site/disks/ive_dmr_prednv_009/${USER}/bios_knob_hwp"
# ---- END OF EDITABLE SECTION -------------------------------------------------

echo "===================================================================="
echo "  BIOS Knob Setup: HWP Enable for TPMI PSS Tests"
echo "===================================================================="
echo ""
echo "Source IFWI dir : ${IFWI_SOURCE_DIR}"
echo "Destination     : ${DEST_DIR}"
echo ""

# Step 1: Create destination directory
echo "[Step 1] Creating destination directory..."
mkdir -p ${DEST_DIR}
if ($status != 0) then
    echo "ERROR: Failed to create ${DEST_DIR}"
    exit 1
endif
echo "         OK: ${DEST_DIR}"

# Step 2: Check source files exist
echo "[Step 2] Checking source IFWI binaries..."
if (! -f "${IFWI_SOURCE_DIR}/${IFWI_S0_BASENAME}") then
    echo "ERROR: Socket 0 IFWI not found:"
    echo "       ${IFWI_SOURCE_DIR}/${IFWI_S0_BASENAME}"
    echo ""
    echo "TIP: List available IFWIs with:"
    echo "     ls ${IFWI_SOURCE_DIR}/*.bin | grep -i hwp"
    exit 1
endif
if (! -f "${IFWI_SOURCE_DIR}/${IFWI_S1_BASENAME}") then
    echo "ERROR: Socket 1 IFWI not found:"
    echo "       ${IFWI_SOURCE_DIR}/${IFWI_S1_BASENAME}"
    exit 1
endif
echo "         OK: both source files found"

# Step 3: Copy IFWIs to destination
echo "[Step 3] Copying IFWI binaries to ${DEST_DIR}..."
cp "${IFWI_SOURCE_DIR}/${IFWI_S0_BASENAME}" "${DEST_DIR}/"
if ($status != 0) then; echo "ERROR: cp failed for S0 IFWI"; exit 1; endif
cp "${IFWI_SOURCE_DIR}/${IFWI_S1_BASENAME}" "${DEST_DIR}/"
if ($status != 0) then; echo "ERROR: cp failed for S1 IFWI"; exit 1; endif
echo "         OK"

# Step 4: Create softlinks expected by CRT (-io IFWI= requires ifwi1.bin + ifwi2.bin)
echo "[Step 4] Creating softlinks ifwi1.bin -> S0  and  ifwi2.bin -> S1 ..."
cd ${DEST_DIR}
if (-l ifwi1.bin) rm -f ifwi1.bin
if (-l ifwi2.bin) rm -f ifwi2.bin
ln -s "${IFWI_S0_BASENAME}" ifwi1.bin
ln -s "${IFWI_S1_BASENAME}" ifwi2.bin
echo "         OK"

# Step 5: Verify
echo ""
echo "[Step 5] Verification:"
ls -la ${DEST_DIR}/
echo ""

echo "===================================================================="
echo "  BIOS knob IFWI directory ready:"
echo "    ${DEST_DIR}"
echo ""
echo "  Required knob in this IFWI:"
echo "    ProcessorHWPMEnable = 1   (HWP / Hardware P-States)"
echo ""
echo "  If you need to modify a different IFWI using XmlCli:"
echo "    Reference: https://wiki.ith.intel.com/spaces/PPA/pages/1774958664"
echo "    Key XmlCli commands:"
echo "      python3 XmlCli.py --knob 'ProcessorHWPMEnable=1' --ifwi <path>.bin"
echo "      (creates <path>_modified.bin with the knob changed)"
echo ""
echo "  Update your .csh run files to use:"
echo "    -io IFWI=${DEST_DIR} --"
echo "===================================================================="

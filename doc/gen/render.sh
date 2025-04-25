#!/bin/sh

fixup_pcb() {
  # kicad-cli pcb render does not honor the "DNP" or "NotInPos"
  # attributes, hence we hide all DNP 3D models prior to rendering:
  python - "$1" <<__PARROT__
import pcbnew
import sys
board = pcbnew.LoadBoard(sys.argv[1])
for fp in board.GetFootprints():
    if fp.IsDNP():
        for index, model in enumerate(fp.Models()):
            fp.Models()[index].m_Show = False
            print(f"Hide 3D model #'{index+1}' of {fp.GetReference()}.")
pcbnew.SaveBoard(sys.argv[1], board)
__PARROT__
}

render() {
  kicad-cli pcb render -o "$2" --quality basic --zoom 1.431 --width 2500 --height 1800 "$1"
}

pcb_orig="$(dirname "$0")/../../demo/kivar-demo.kicad_pcb"
pcb_nochange=$(mktemp --suffix .kicad_pcb)
pcb_change=$(mktemp --suffix .kicad_pcb)

kivar set -v \
  -A 'BOOT_SRC=NAND' \
  -A 'EEPROM_ADDR=0x54' \
  -A 'I_LED_MA=70' \
  -A 'IOEXP_TYPE/ADDR=9535/0x24' \
  -A 'ISL91127=IRNZ' \
  -A 'UVLO_LO/HI=3.15V/3.57V' \
  -A 'VOUT=1.8V' \
  -o "$pcb_nochange" "$pcb_orig"
fixup_pcb "$pcb_nochange"
render "$pcb_nochange" "$(dirname "$0")/../pcb-nochange.png"

# TODO changes according to certain variant!
kivar set \
  -A 'BOOT_SRC=EMMC' \
  -A 'EEPROM_ADDR=0x55' \
  -A 'I_LED_MA=110' \
  -A 'IOEXP_TYPE/ADDR=9535/0x24' \
  -A 'ISL91127=IRAZ' \
  -A 'UVLO_LO/HI=3.15V/3.57V' \
  -A 'VOUT=3.3V' \
  -o "$pcb_change" "$pcb_orig"
fixup_pcb "$pcb_change"
render "$pcb_change" "$(dirname "$0")/../pcb-change.png"

rm "$pcb_nochange" "$pcb_change"

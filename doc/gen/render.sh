#!/bin/sh -e

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
  kicad-cli pcb render -o "$2" --quality basic --zoom 1.44 --width 2500 --height 1800 "$1"
}

kivar_cli="$(dirname "$0")/../../source/kivar_cli.py"
pcb_orig="$(dirname "$0")/../../demo/kivar-demo.kicad_pcb"
pcb_nochange=$(mktemp --suffix .kicad_pcb)
pcb_change=$(mktemp --suffix .kicad_pcb)

python "$kivar_cli" set -v -V 'Series 1000' -o "$pcb_nochange" "$pcb_orig"
fixup_pcb "$pcb_nochange"
render "$pcb_nochange" "$(dirname "$0")/../pcb-nochange.png"

python "$kivar_cli" set -v -V 'Series 5000 Basic' -o "$pcb_change" "$pcb_orig"
fixup_pcb "$pcb_change"
render "$pcb_change" "$(dirname "$0")/../pcb-change.png"

rm "$pcb_nochange" "$pcb_change"

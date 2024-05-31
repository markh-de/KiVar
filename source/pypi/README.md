# KiVar − PCB Assembly Variants for KiCad

## Introduction

KiVar is a tool for **KiCad PCB Assembly Variant selection**, provided as platform-independent

 * **Command Line Application** (this package) and
 * **KiCad Action Plugin** (available in KiCad PCM).

PCB component variation rules are defined in component (i.e. symbol or footprint) fields.  This allows for the complete variant configuration to be contained in the schematic and board files without requiring external data from outside the native KiCad design files.

The name _KiVar_ (for _KiCad Variants_, obviously) can also be read as an acronym for _**Ki**Cad **V**ariation **a**ssignment **r**ules_.

## Features

KiVar assigns PCB component **values**, **field content** and **attributes** (such as _Do not populate_, _Not in position files_, _Not in BoM_) according to variation rules specified in footprint fields.  When applying those rules, components are modified _in place_, allowing for immediate update of the PCB design as well as the 3D view and enabling compatibility with _any_ exporter.

Back-propagation of modified component data from the PCB to the schematic can be done in an extra step.

## What to Expect

Example usage of the **KiVar Command Line Interface app**:

```
$ kivar list --selection kivar-demo.kicad_pcb 
BOOT_SRC: [EMMC] JP NAND SD
EEPROM_ADDR: 0x54 [0x55]
I_LED_MA: 10 20 30 40 50 60 70 80 90 [100] 110 120 130 140 150 JP
IOEXP_TYPE/ADDR: 9535/0x20 [9535/0x24] 9539/0x74
ISL91127: [IRAZ] IRNZ
UVLO_LO/HI: 2.41V/3.40V [3.15V/3.57V]

$ kivar set --assign 'I_LED_MA=60' --assign 'BOOT_SRC=NAND' --verbose kivar-demo.kicad_pcb 
Changes (16):
    Change R9 'Do not populate' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R9 'Exclude from bill of materials' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R9 'Exclude from position files' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R9 field 'ChoiceText' from 'SoM eMMC' to 'SoM NAND' (BOOT_SRC=NAND).
    Change R10 'Do not populate' from 'true' to 'false' (BOOT_SRC=NAND).
    Change R10 'Exclude from bill of materials' from 'true' to 'false' (BOOT_SRC=NAND).
    Change R10 'Exclude from position files' from 'true' to 'false' (BOOT_SRC=NAND).
    Change R11 'Do not populate' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R11 'Exclude from bill of materials' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R11 'Exclude from position files' from 'false' to 'true' (BOOT_SRC=NAND).
    Change R21 'Do not populate' from 'false' to 'true' (I_LED_MA=60).
    Change R21 'Exclude from bill of materials' from 'false' to 'true' (I_LED_MA=60).
    Change R21 'Exclude from position files' from 'false' to 'true' (I_LED_MA=60).
    Change R22 'Do not populate' from 'true' to 'false' (I_LED_MA=60).
    Change R22 'Exclude from bill of materials' from 'true' to 'false' (I_LED_MA=60).
    Change R22 'Exclude from position files' from 'true' to 'false' (I_LED_MA=60).
Board saved to file "kivar-demo.kicad_pcb".

$ kivar list --selection kivar-demo.kicad_pcb 
BOOT_SRC: EMMC JP [NAND] SD
EEPROM_ADDR: 0x54 [0x55]
I_LED_MA: 10 20 30 40 50 [60] 70 80 90 100 110 120 130 140 150 JP
IOEXP_TYPE/ADDR: 9535/0x20 [9535/0x24] 9539/0x74
ISL91127: [IRAZ] IRNZ
UVLO_LO/HI: 2.41V/3.40V [3.15V/3.57V]
```

## Concepts

Key concepts of KiVar are:

 * Designs may contain **multiple** independent variation **aspects** (i.e. dimensions or degrees of freedom).
 * Variation rules are **fully contained** in component fields of native design files (no external configuration files) and **portable** (i.e. copying components to another design keeps their variation specification intact).
 * Component values, fields and attributes are modified **in place**, enabling compatibility with all exporters that work on the actual component data.
 * **No external state information** is stored; currently matching variation choices are detected automatically.

## Project Page

For the usage manual and a demo project check out the [KiVar Project Page](https://github.com/markh-de/KiVar).

# KiVar − PCB Assembly Variants for KiCad

## Introduction

KiVar is a tool for **KiCad PCB Assembly Variant selection**, provided as platform-independent

 * **Command Line Application** (this package) and
 * **KiCad Action Plugin** (available in KiCad PCM).

PCB component variation rules are defined in component (i.e. symbol or footprint) fields.  This allows for the complete variant configuration to be contained in the schematic and board files without requiring external data from outside the native KiCad design files.

## Features

KiVar assigns PCB component **values**, **field content**, **attributes** (such as _Do not populate_, _Not in position files_ or _Not in BoM_) and **features** (such as _individual 3D model visibility_ or _solder paste application_) according to variation rules specified in footprint fields.  When applying those rules, components are modified **in place**, allowing for immediate update of the PCB design as well as the 3D view and enabling compatibility with _any_ exporter.

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
VOUT: 1.2V [1.8V] 3.3V

$ kivar set --assign 'IOEXP_TYPE/ADDR=9539/0x74' --assign 'VOUT=3.3V' --verbose kivar-demo.kicad_pcb 
Changes (14):
    Change R38 value from '100kΩ' to '175kΩ' (VOUT=3.3V).
    Change R38 field 'VarID' from '18' to '33' (VOUT=3.3V).
    Change R39 value from '100kΩ' to 'DNP' (VOUT=3.3V).
    Change R39 'Do not populate' from 'false' to 'true' (VOUT=3.3V).
    Change R39 'Exclude from bill of materials' from 'false' to 'true' (VOUT=3.3V).
    Change R39 'Exclude from position files' from 'false' to 'true' (VOUT=3.3V).
    Change R39 solder paste relative clearance from 0.0% to -4200000.0% (VOUT=3.3V).
    Change U4 value from 'TCA9535PWR' to 'TCA9539PWR' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 visibility of 3D model #1 from 'true' to 'false' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 visibility of 3D model #2 from 'false' to 'true' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 field 'I2C Address' from '0x24' to '0x74' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 field 'VarID' from '24' to '74' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 field 'Datasheet' from 'http://www.ti.com/lit/ds/symlink/tca9535.pdf' to 'http://www.ti.com/lit/ds/symlink/tca9539.pdf' (IOEXP_TYPE/ADDR=9539/0x74).
    Change U4 field 'MPN' from 'TCA9535PWR' to 'TCA9539PWR' (IOEXP_TYPE/ADDR=9539/0x74).
Board saved to file "kivar-demo.kicad_pcb".

$ kivar list --selection kivar-demo.kicad_pcb 
BOOT_SRC: [EMMC] JP NAND SD
EEPROM_ADDR: 0x54 [0x55]
I_LED_MA: 10 20 30 40 50 60 70 80 90 [100] 110 120 130 140 150 JP
IOEXP_TYPE/ADDR: 9535/0x20 9535/0x24 [9539/0x74]
ISL91127: [IRAZ] IRNZ
UVLO_LO/HI: 2.41V/3.40V [3.15V/3.57V]
VOUT: 1.2V 1.8V [3.3V]

$ kivar check kivar-demo.kicad_pcb 
Check passed.  Matching choices found for complete set of 7 aspect(s).

$ kivar state --query VOUT --query EEPROM_ADDR kivar-demo.kicad_pcb 
3.3V
0x55
```

The KiVar CLI provides support for 

 * setting,
 * querying,
 * listing and
 * analyzing

variation data, either manually or - for example - integrated in a Continuous Integration service.

## Concepts

Key concepts of KiVar are:

 * Designs may contain **multiple** independent variation **aspects** (i.e. dimensions or degrees of freedom).
 * Variation rules are **fully contained** in component fields of native design files (no external configuration files involved) and **portable** (i.e. copying components to another design keeps their variation specification intact).
 * Component values, fields, attributes and features are modified **in place** with immediate effect, enabling compatibility with all exporters that work on the actual component data.
 * **No external state information** is stored; currently matching variation choices are detected automatically.

## Supported KiCad Versions

KiVar requires the _pcbnew_ Python module of at least **KiCad release 8**.

## Project Page

For the usage manual and a demo project check out the [KiVar Project Page](https://github.com/markh-de/KiVar).

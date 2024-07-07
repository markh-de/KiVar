# KiVar − PCB Assembly Variants for KiCad

## Introduction

<img align='right' style='width:6em;' src='doc/kivar-icon.inkscape.svg'>

KiVar is a tool for **KiCad PCB Assembly Variant selection**, provided as platform-independent

 * **KiCad Action Plugin** and
 * **Command Line Application**.

PCB component variation rules are defined in component (i.e. symbol or footprint) fields.  This allows for the complete variant configuration to be contained in the schematic and board files without requiring external data from outside the native KiCad design files.

The name _KiVar_ (for _KiCad Variants_, obviously) can also be read as an acronym for _**Ki**Cad **V**ariation **a**ssignment **r**ules_.

## Features

KiVar assigns PCB component **values**, **field content** and **attributes** (such as _Do not populate_, _Not in position files_, _Not in BoM_) according to variation rules specified in footprint fields.  When applying those rules, components are modified _in place_, allowing for immediate update of the PCB design as well as the 3D view and enabling compatibility with _any_ exporter.

Back-propagation of modified component data from the PCB to the schematic can be done in an extra step.

## What to Expect

### KiCad Action Plugin

Example selection dialog of the **KiVar Action Plugin for KiCad**:

![KiVar Action Plugin Example](doc/plugin-changes.svg)

### Command Line Interface Application

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

## Supported KiCad Versions

KiVar releases 0.2.0 and later require at least **KiCad release 8**.

Earlier versions of KiVar also supported KiCad 7, but in a very restricted way.  Hence, after the release of KiCad 8, KiVar support for KiCad 7 has been dropped.

KiVar uses the Python API wrapper for pcbnew, the KiCad PCB Editor.

## Installation

### KiVar Action Plugin

The recommended plugin installation method is to use KiCad's integrated **Plugin and Content Manager**.  KiVar is included in the **official PCM repository**, allowing a smooth and safe installation and update experience.  For manual installation users can also choose to download the plugin archive package.

#### Using the Plugin and Content Manager

Required steps:

1. Start the _Plugin and Content Manager_ from the KiCad main window.
2. Find _KiVar_ in the **Plugins** section.
3. Mark it for installation and apply the pending changes.
4. The _KiVar_ plugin icon should now appear in the PCB Editor (pcbnew) toolbar.

#### Using Manual Archive Extraction

Required steps:

1. Open the KiCad PCB Editor (pcbnew).
2. In the PCB Editor, choose the menu option _Tools &rarr; External Plugins &rarr; Open Plugin Directory_.  This will open a file browser at the location of your KiCad plugin directory.
3. Unzip the contents of an official [KiVar release archive](https://github.com/markh-de/KiVar/releases) (the ZIP file _without_ the `-pcm` suffix) to that KiCad plugin directory you opened in the previous step.  _Important:_ Do not create another directory inside the target plugin directory, but only place the files from the release archive directly in the plugin directory.
4. Switch back to the PCB Editor and choose the menu option _Tools &rarr; External Plugins &rarr; Refresh Plugins_.  The _KiVar_ plugin icon should now appear in the toolbar and in the plugin list under _Tools &rarr; External Plugins_.

If the installation does not work for you this way, consider reporting your problem as an issue in the KiVar bug tracker.

### KiVar Command Line Application

#### Using pip

The KiVar CLI (command line interface) Python package can be installed using the following methods.

##### From the PyPI Repository

To install the latest KiVar CLI app from the official KiVar PyPI repository, open a shell and run:

```
pip install kivar
```

##### From a Release Archive

The KiVar CLI app can also be installed using a downloaded (or locally created) Python Package (replace `${VERSION}` by the actual package version):

```
pip install kivar-${VERSION}.tar.gz
```

## Usage

> [!IMPORTANT]
> This manual refers to the **0.2.x** series of KiVar, which uses different component fields for specifying rules, a slightly modified (but significantly extended) rule syntax, and an enhanced range of functions compared to earlier versions.  
> If you are still using an older version, please consider [updating](#installation) KiVar and [migrating](#migrate) your variation rules to the new format.  
> You can also switch to the [latest version of this user guide](https://github.com/markh-de/KiVar/blob/main/README.md#usage).

The process of writing and assigning rules to components (i.e. symbols and footprints) is done manually using simple text expressions.

Once all relevant components are equipped with their variation rules, KiVar allows the selection of variation choices using either an easy-to-use dialog interface (when using the Action Plugin) or a command-line interface (when using the CLI app) and takes care of the automatic analysis and assignment of the corresponding component values, fields and attributes.

The following sections describe the process of configuring your schematic or board and - after that - selecting a variation configuration from the previously configured variation choices.

### Component Variation Setup

The following sub-sections describe the variation rules setup procedure.

While it is recommended to define variation rules in the schematic (i.e. in symbol fields) and propagate them to the board, it is also possible to define those rules directly in the board (i.e. in footprint fields) and propagate them back to the schematic.  Either way, in order for KiVar to utilize the variation rules, they must be present in the footprint fields, as KiVar uses the _pcbnew_ API wrapper and can therefore only operate on the board (not schematic) data, which must then be [propagated back to the schematic](#updating-the-schematic).

> [!TIP]
> If you are already experienced with writing variation rules for older KiVar 0.1.x versions, it is highly recommended to read the [KiVar Migration Guide](#migrate), which covers the most important changes introduced with KiVar release 0.2.0.

#### Definition of Terms

<!-- don't repeat
As mentioned before, KiVar supports multiple independent _variation aspects_ per board.  For each of these variation aspects, one _variation choice_ can be made later during the selection process.  The result of selecting a specific set of choices for a given set of aspects forms a _variation configuration_.
-->

Basic terms used in this document:

 * **Aspect:**  
   A dimension of variation changes, which are defined by _Choices_ (see below).  One PCB design can refer to multiple aspects.  Each component, which makes use of KiVar variations, must refer to exactly one aspect identifier.  
   For example, an Aspect can be the I²C address of an EEPROM IC, using an identifier like `EEPROM_I2C_ADDR`.
 
 * **Choice:**  
   A set of values (component values or field contents) and/or properties to be assigned to specific components.  A Choice is always related to a specific _Aspect_.  
   For example, possible Choices for the I²C address Aspect could be `0x50`, `0x51`, `0x52`, `0x53`.

 * **Configuration:**  
   A fully defined selection of _specific_ _Choices_ for _all_ available _Aspects_.  In other words, one specific board assembly variant state.  
   An example is shown in the following section.

#### Fundamentals

Each component (which uses KiVar variation rules) must refer to exactly one **Aspect**, to which all **Choices** defined or referred to in that component always relate to.

There can exist multiple Aspects per design, and for each Aspect there can exist multiple Choices.

_Example:_

 * Aspect `EEPROM_I2C_ADDR`
   * Choice `0x50`
   * Choice `0x51`
   * Choice `0x52`
   * Choice `0x53`

 * Aspect `BOOT_SRC`
   * Choice `EMMC`
   * Choice `SDCARD`
   * Choice `NAND`

 * Aspect `VIO_LEVEL`
   * Choice `1.8V`
   * Choice `2.5V`
   * Choice `3.3V`

One possible example _Configuration_ for these Aspects and Choices:

`EEPROM_I2C_ADDR=0x52 BOOT_SRC=NAND VIO_LEVEL=1.8V`

KiVar computes such sets of Aspect and Choice definitions internally by checking each component's field data for KiVar [Choice Expressions](#choice-expressions), which are explained in the following sections.

#### Choice Expressions

Component variation rules are specified in **Choice Expression**s, which are defined in the fields of each component (i.e. symbol and/or footprint) they relate to.  Multiple components may (and usually will) refer to the same aspects and choices.

One component must relate to a single aspect, but can relate to an unlimited number of choices for that aspect.

Typically, multiple components are involved when defining specific Choices.  But not each component is forced to refer to all Choices (of a certain Aspect).  Instead, the KiVar Expression compiler accumulates all mentioned Choices and computes the data to be assigned for each of them.

Choice Expressions can use various notations, depending on their Scope and Format.  Choice Expression syntax is described in the following sections from their **innermost to outermost** elements.

#### Choice Arguments

In its simplest form, a Choice Expression consists only of a **Choice Argument List**, which is just a list of _space_-separated **Choice Argument**s to be assigned to a component for a specific choice.

Each _Choice Argument_ of the _Choice Argument List_ can be of one of two possible types:
 * a part of the **Content** to be assigned as the component _value_ or a specific target _field_, or
 * a **Property** state assignment specifier (e.g. to mark a component _(un)fitted_, _(not) in BoM_, _(not) in position files_).

Argument types are distinguished by their first (unescaped) character and will be explained in more detail in the following sub-sections.

##### Content Specifiers

###### Purpose

One or more **Content Specifiers** can be used to form a string to be assigned to the component value or to any (custom) component field (such as _Manufacturer_, _MPN_, ...).

###### Syntax

Each argument beginning with a character _other than_ `-` and `+` is interpreted as a **Content Specifier**.

There can be multiple Content Specifiers in each Choice Expression.  Their values will be concatenated with one ` ` (space) character as separator to form the resulting Content string.  However, each choice may have only a maximum of one resulting Content assigned.  For example: `Choice1("hello world"   foo bar)` will result in `Choice1` to be assigned the content `hello world foo bar`, but multiple content assignments to the same Choice, such as `Choice1("hello world") Choice1(foo bar)`, are invalid.  This restriction is due to the fact that Choice Expressions can be provided in different ([Simple](#simple), [Combined](#combined)) formats and there is no guaranteed processing (concatenation) order.

###### Evaluation

All Content Specifiers of a Choice Expression are evaluated from left to right and concatenated with one space character between each argument to form the final content string to be assigned when the corresponding choice is selected.

> [!NOTE]
> As arguments can be separated by _any_ number of space characters, each separation will result in a single space character in the final content, no matter how many spaces were used for the argument separation originally (similar to HTML).  For strings that shall be assigned in a verbatim way (such as a URL), it is highly recommended to use quoting techniques (discussed later).

###### Examples

The Content Specifiers in the following input Choice Argument Lists will result in the following Content strings:

Choice Argument List input | Resulting Content string | Explanation
-------------------------- | ------------------------ | -----------
`100nF`                    | `100nF`                  | Simple single arguments can be noted without escaping or quoting as long as they don't contain certain special characters (discussed later).
`470µF 10%`                | `470µF 10%`              | Uncritical text, no verbatim adoption of the arguments required.
`470µF   10%`              | `470µF 10%`              | Multiple separator characters will be converted to a single separator. As the text is uncritical, this conversion may even be desired.
`'https://kivar.markh.de/ds/abc123.pdf'` | `https://kivar.markh.de/ds/abc123.pdf` | Strings to be used verbatim should always be enclosed in quote characters.
`'abc   def ' 123   456`   | `abc   def  123 456`     | Mixed type of quoted and unquoted representation.  Note how the trailing space after `def` remains contained in the result.
`abc "def 'ghi' jkl" mno`  | `abc def 'ghi' jkl mno`  | Outer double quotes encapsulate inner single quotes, which are part of the verbatim string.
`abc 'def "ghi" jkl' mno`  | `abc def "ghi" jkl mno`  | Outer single quotes encapsulate inner double quotes, which are part of the verbatim string.
`abc \d\e\f\ \ ghi\'jkl\\mno` | `abc def  ghi'jkl\mno` | Escaping (prepending a backslash) ensures that the following character is interpreted verbatim, not as a special character.  To create a backslash (the escape character) string, use a double backslash (i.e. escape the backslash).
`\+10% \-5% \-12V \+5V`    | `+10% -5% -12V +5V`      | If the first character of a Content Specifier is a `-` or `+`, the corresponding Choice Argument must be prepended with a backslash (`\`) character or be part of a verbatim string (see next example).
`"+10%" '-5%' "-"12V '+'5V` | `+10% -5% -12V +5V`     | If the first character of a Content Specifier is a `-` or `+`, the corresponding Choice Argument must be part of a verbatim string or be prepended with a backslash (`\`) character (see previous example).

##### Property Specifiers

###### Purpose

KiVar provides a set of boolean component _Properties_ that allow controlling the component attributes

 * **Do not Populate**,
 * **Not in Position Files**, and
 * **Not in BoM**
 
as well as component features, such as

 * **Individual 3D Model Appearance** and
 * **Solder Paste Application**.

###### Syntax

Each argument beginning with a `-` or `+` is interpreted as a **Property Specifier**, which is a combination of **Property Modifiers** and **Property Identifiers**.

Each Property Specifier must start with a _Property Modifier_, defining the boolean state (_true_ or _false_, represented by `+` or `-`, respectively) to be assigned to the Properties subsequently specified by their corresponding _Property Identifiers_.

###### Evaluation

All Property Specifiers inside a Choice Expression are evaluated from left to right, resulting in a set of defined boolean Property states for the corresponding component and Choice.  Properties _not_ defined in any of the component's Choices are kept in their original state.

###### Attribute Properties

The following Properties allow modification of component _attributes_:

 * **Fitted** (property identifier `f`).  
   This property specifies whether a component shall be fitted (property state _true_) or unfitted (property state _false_).  This property is linked to the pcbnew footprint attribute _Do not populate_ with inverted polarity.
 * **inPos** (property identifier `p`).  
   This property specifies whether a component shall be included in the component placement/position files (property state _true_) or excluded (property state _false_).  This property is linked to the pcbnew footprint attribute _Not in Position Files_ with inverted polarity.
 * **inBom** (property identifier `b`).  
   This property specifies whether a component shall be included in the Bill of Materials (property state _true_) or excluded (property state _false_).  This property is linked to the pcbnew footprint attribute _Not in BoM_ with inverted polarity.

###### Feature Properties

Additionally, the following Properties allow controlling component _features_:

 * **Model** (property identifier `mN`, with `N` being an integer number).  
   This property controls the visibility of each individual 3D model of the corresponding component footprint to either visible (property state _true_) or invisible (property state _false_).  An integer number must be provided directly following the first character of the property identifier, representing the index of the model to be shown or hidden.  The index starts at 1.
 * **Solder** (property identifier `s`).  
   This property controls the application of solder paste to the pads of a component's footprint.  Solder paste can be enabled (property state _true_) or disabled (property state _false_).  For both cases, user-defined footprint-specific solder paste clearances are maintained (see note below).  _Important:_ As usual for KiCad solder paste clearance settings, this property has only effect for pads on copper layers, but _not_ for _SMD Aperture_ pads!

> [!NOTE]
> As KiCad does not provide a dedicated footprint attribute for disabling solder paste application, KiVar instead makes use of the _solder paste relative clearance_ value.  To disable or enable solder paste application for a footprint, KiVar applies or removes an offset value of &minus;4,200,000%.  This technique allows retaining user-provided clearance values.  However, in order to ensure safe classification of KiVar-applied solder paste control, those user-provided relative clearance values are only allowed in the range from &minus;10,000% to &plus;10,000%.

###### Group Properties

The following Property allows grouping frequently used attribute properties for user convenience:

 * **Assemble** (property identifier `!`).  
   This Group Property represents all three attribute properties **Fitted**, **inPos** and **inBom** (`f`, `p`, `b`).  It can be used as a shortcut, as most of the times all three attributes are controlled together and set to the same state when a component is switched between _assembled_ or _unassembled_.  However, if finer control is desired, the state of individual attribute properties can still be overridden.  Examples can be found in the next section.

###### Examples

The Property Specifiers in the following input Choice Argument Lists will result in the following Property states:

Choice Argument List input | Resulting Property states | Explanation
-------------------------- | ------------------------- | -----------
`-f`                       |  _not_ Fitted             | The `-` causes _false_ to be assigned to the subsequent properties, i.e. _Fitted_.  The footprint's attribute _Do not populate_ will be set to _true_.
`-fbp`                     |  _not_ Fitted, _not_ inBom, _not_ inPos | One modifier (`-`) can be used for any number of subsequent identifiers.
`-!`                       |  _not_ Fitted, _not_ inBom, _not_ inPos | Equivalent to prior example.
`+!`                       |  Fitted, inBom, inPos     | Place this component to the board, include it in the BoM and in position files.
`-! +b`                    |  _not_ Fitted, inBom, _not_ inPos | After setting `f`, `b`, `p` to false, `b` is set to true again.  Useful if you want your BoM to include unfitted parts, that are otherwise marked "DNP".
`-!+b`                     |  _not_ Fitted, inBom, _not_ inPos | Equivalent to prior example.  Multiple modifiers may appear inside a single specifier argument.

#### Choice Identifiers

##### Purpose

Each Choice must have a unique name within its Aspect scope.  This name can be any string.

For referring to a Choice name, **Choice Identifiers** are used.  They are basically the same as the name itself, but rules for [quoting and escaping](#quoting-and-escaping) of special characters apply.  Choice Identifiers are **case-sensitive**.

Whether the mention of a Choice Identifier implicitly declares the Choice in its Aspect context depends on the scope in which the identifier is used:  
In [Base Scope](#base), expressions can declare (new) choice identifiers, while in [Auxiliary Scope](#aux), expressions can only refer to Choice Identifiers declared in [Base Scope](#base) (in the same or another component).

The special Choice Identifier `*` is used for specifying default Content and Properties to be applied to Choices not explicitly listed in the corresponding assignment.  Refer to the [Default Choices](#default-choices) section below for details.

##### Declaration and Definition

<!-- TODO this is important to understand. explain how declaration of choices can be done by _any_ component's Base Scope expression in the same aspect scope and how the list of available choices is automatically extended. old text! update and use rule compiler figure from demo project? -->

<!-- TODO update demo figure for each expression type, use same colors for identification of example elements. -->

##### Choice Identifier Lists

When using Choice Identifiers in Choice Expressions, those identifiers are always specified inside **Choice Identifier Lists**.  A Choice Identifier List consists of **one or more** Choice Identifiers that are separated by `,` (comma) characters (e.g. `ChoiceId_1,ChoiceId_2,ChoiceId_3`).  No space is allowed around the separating comma.

##### Default Choices

###### Purpose

To follow the ["All-or-None" rule](#all-or-none), Content and Property assignments must be defined for _all_ choices involved if at least one assignment is defined.

Defining all Choices for each assignment theoretically requires each Choice Identifier to be listed along with its corresponding Content or Property assignments.  Also, any modification of available Choice Identifiers (i.e. adding, removing, renaming Choices) in _one_ component theoretically requires the Choice Expressions of _all_ components in the same Aspect scope to be adapted as well.

To avoid listing each possible Choice Identifier for each assignment, **Default Choices** can be used.  The Content and Property assignments specified for a Default Choice apply as described below.

###### Syntax

The reserved Choice Identifier used for Default Choices is "`*`".

###### Default Content Inheritance

For each assignment target, the Content (component value or field content, respectively) specified in the Default Choice applies to all Choices that **do not provide** their own Content definition for the same assignment.

The following table explains Content inheritance rules using an example Choice Identifier `A` and some example Content.

Default Choice (`*`) Content | Specific Choice (`A`) Content | Resulting Specific Choice (`A`) Content
---------------------------- | ----------------------------- | ---------------------------------------
_(none)_                     | _(none)_                      | _(none)_
_(none)_                     | `123`                         | `def`
`abc`                        | _(none)_                      | `abc`
`abc`                        | `123`                         | `123`

###### Default Property Inheritance

For each assignment target, the state of each Property specified in the Default Choice is used as the **initial value** for _all_ Choices with the same assignment target.

The following table explains Property state inheritance rules using an example Choice Identifier `B` and some example Property states (with resulting Property states listed with [Property Specifier](#property-specifiers) syntax).

Default Choice (`*`) Property Specifiers | Specific Choice (`B`) Property Specifiers | Resulting Specific Choice (`B`) Property states
---------------------------------------- | ----------------------------------------- | -----------------------------------------------
_(none)_                                 | _(none)_                                  | _(none)_
_(none)_                                 | `+f`                                      | `+f`
`+f`                                     | _(none)_                                  | `+f`
`+!`                                     | _(none)_                                  | `+fbp` _([&rarr; group](#group-properties))_
`+!`                                     | `-p`                                      | `+fb` `-p`
`+f`                                     | `-b`                                      | `+f` `-b`
`+f +b`                                  | `-b`                                      | `+f` `-b`

##### Implicit Defaults

For Property assignments, it may not be required to explicitly specify a Default Choice, as for Properties, **Implicit Defaults** may apply.

For each assignment target, whenever only _one_ state (i.e. _either_ `+` _or_ `-`) is assigned to a specific Property, then the **opposite** state is used for this Property as the Implicit Default for that assignment.

> [!NOTE]
> The Implicit Default can be imagined as a "Default Default", i.e. the _Implicit_ Default state of a Property will be **overridden** by a state specified in an _explicit_ (usual) [Default Choice](#default-choices).

> [!NOTE]
> Implicit Defaults are only used for Properties, _not_ for Content, as Properties are boolean values and therefore have an "opposite" value that can be assumed as the desired Default state.

The following table explains Implicit Default state inheritance rules using the example Choice Identifiers `C1`, `C2`, `C3`.  `C3` is not defined, but declared, hence its Property states (PS) will be assigned a value if Default states (implicit or explicit) exist.  Resulting Property states ("RPS") are listed with [Property Specifier](#property-specifiers) syntax).

Choice `C1` PS | Choice `C2` PS | Implicit Default PS                                      | Default (`*`) PS | `C1` RPS  | `C2` RPS  | `C3` RPS
-------------- | -------------- | -------------------------------------------------------- | ---------------- | --------- | --------- | ---------
_(none)_       | _(none)_       | _(none)_                                                 | _(none)_         | _(none)_  | _(none)_  | _(none)_
`+f`           | _(none)_       | `-f` _(opposite of C1)_                                  | _(none)_         | `+f`      | `-f`      | `-f`
`+f`           | `+f`           | `-f` _(opposite of C1/C2)_                               | _(none)_         | `+f`      | `+f`      | `-f`
`+f`           | `-f`           | _(none)_ _(C1/C2 contradicting)_                         | _(none)_         | `+f`      | `-f`      | _(none)_ (Invalid! `f` missing!)
`+f`           | `-f`           | _(none)_                                                 | `-f`             | `+f`      | `-f`      | `-f`
`+f`           | `-p`           | `-f` `+p`                                                | _(none)_         | `+f` `+p` | `-f` `-p` | `-f` `+p`
`-!`           | _(none)_       | `+fbp` _([&rarr; group](#group-properties))_ | _(none)_         | `-fbp`    | `+fbp`    | `+fbp`
`-!`           | `-p`           | `+fbp`                                                   | _(none)_         | `-fbp`    | `+fb` `-p`| `+fbp`
`+f`           | _(none)_       | `-f`                                                     | `+b`             | `+f` `+b` | `-f` `+b` | `-f` `+b`
`-!`           | `+p`           | `+fb` _(`p` contradicting)_                              | _(none)_         | `-fbp     | `+fb` `+p`| `+fb` (Invalid! `p` missing!)
`-!`           | `+p`           | `+fb`                                                    | `-p`             | `-fbp     | `+fb` `+p`| `+fb` `-p`

<!-- TODO more (creative) examples -->

#### Choice Expression Scopes

The data defined in Choice Expressions can be applied to either
 * the component's basic properties (i.e. component _value_ and _attributes_), or to
 * custom component fields (such as _Manufacturer_, _MPN_, ...).

For each of them there exists a dedicated **Choice Expression Scope**.  Both scopes are explained in the following sub-sections.

<a name="base"></a>

##### Base Scope

###### Purpose

Expressions in **Base Scope** are used to
 * assign component **values** (using [Content Specifiers](#content-specifiers)) and **attributes** (using [Property Specifiers](#property-specifiers)), and to
 * **declare** and **define** [Choice Identifiers](#choice-identifiers) in the context of a corresponding [Aspect Identifier](#aspect-identifier).

###### Typical Use

The Base Scope is used to assign basic component values, such as `10kΩ`, `0.1µF 50V` or `74HC595`, to the mandatory "Value" field of a component (i.e. symbol or footprint), passed via [Content Specifiers](#content-specifiers).

Also, the Base Scope is used to modify component attributes, for example to modify the _DNP_ (Do Not Populate), _Exclude from Position Files_ and/or _Exclude from BoM_ states (attributes) of a component.  Component attributes are modified using [Property Specifiers](#property-specifiers).

> [!IMPORTANT]
> Expressions in the Base Scope can _not_ modify **custom** (i.e. other than "Value") fields.  For this, the [Auxiliary Scope](#aux) must be used (see next section).

Examples using the Base Scope are discussed later in the [SBE](#sbe) and [CBE](#cbe) sections.

<a name="aux"></a>

##### Auxiliary Scope

###### Purpose

Expressions in **Auxiliary Scope** (or short: _Aux Scope_) are used for assigning values to specific component **custom** target fields with the use of [Content Specifiers](#content-specifiers).

> [!IMPORTANT]
> Expressions in the Auxiliary Scopy can _not_ declare additional Choice Identifiers, but only refer to existing ones that are declared in the [Base Scope](#base) of the same or any other component using the same Aspect.

> [!IMPORTANT]
> Expressions in the Auxiliary Scope refer to dedicated _target fields_ of components, not to the components themselves.  As target fields do not have mutable attributes, Auxiliary Scope expressions do _not_ support specifying Properties.

> [!IMPORTANT]
> Target fields referenced by Expressions in the Auxiliary Scope _must_ already exist.

> [!NOTE]
> The target field names "Footprint", "Reference" and "Value" are not permitted (to change the component value, the [Base Scope](#base) must be used).

###### Typical Use

The Auxiliary Scope is used to assign custom field values, such as a manufacturer name or a manufacturer product number (MPN), for example, to be used in the bill of materials.

Auxiliary Scope expressions can also be used to specify other information, such as user-defined choice-dependent text information to be visible anywhere in the schematic for documentation purposes (using text-variables).

Examples using the Auxiliary Scope are discussed later in the [SAE](#sae) and [CAE](#cae) sections.

#### Choice Expression Formats

Furthermore, Choice Expressions can use different notations, depending on the user's preferences and requirements.

The two different **Choice Expression Formats** are described in the following sub-sections.

<a name="simple"></a>

##### Simple Format

###### Purpose

The **Simple Format** is particularly well suited to
 * specify a single Choice Expression using
 * one specific component field per expression.

###### Typical Use

Expressions noted in Simple Format
 * are recommended for longer, more complex (or verbatim) Content, such as a datasheet or purchase URL or a complex "Value" field content,
 * can be useful when referencing a dedicated set of Choice Arguments using text variables that are embedded at another location of the schematic (see examples),
 * have the drawback that, due to the diversity of the symbol field names they occupy, each unique used field name adds to the list of field names available in total, for example when using the Symbol Fields Editor.

Examples using the Simple Format are provided in the [SBE](#sbe) and [SAE](#sae) sections.

<a name="combined"></a>

##### Combined Format

The **Combined Format** is particularly well suited to
 * allow combining multiple Choice Expressions in
 * a single component field (also, in [Base Scope](#base), optionally accepting the [Aspect Identifier](#aspect-identifier)).

###### Typical Use

Expressions noted in Combined Format
 * are recommended for shorter, simpler Content, such as a simple component Value, a short MPN or manufacturer name,
 * allow specifying multiple Choice Expressions in a compact way,
 * therefore save space when many Choices need to be declared or defined.

Examples using the Combined Format are provided in the [CBE](#cbe) and [CAE](#cae) sections.

#### Choice Expression Types

The four available **Choice Expression Types** are formed by using both [Expression Scopes](#expression-scopes) with both [Expression Formats](#expression-formats) as discussed in the following sub-sections.

<a name="sbe"></a>

##### Simple Base Expressions (SBE)

###### Typical Use

Using the [Base Scope](#base), **Simple Base Expression**s define the component's Value content and/or component attributes and features.

[Content](#content-specifiers) and [Property](#property-specifiers) specifiers are noted in the [Simple Format](#simple).

###### Syntax

**Field name**: `Var(<CIL>)`

**Field content:** `<CAL>`

Used placeholders:
 * `<CIL>` specifies the [Choice Identifiers List](#choice-identifiers).
 * `<CAL>` specifies the corresponding [Choice Arguments List](#choice-arguments).

###### Examples

The following entries could be used for a capacitor.  Note how the Aspect Identifier must be passed with a dedicated entry, as SBEs cannot include the Aspect Identifier, as is possible for [CBEs](#cbe).

Field name            | Field content
--------------------- | -------------
`Var.Aspect` \*       | `Capacitance`
`Var(Low)`            | `10µF`
`Var(Medium)`         | `100µF`
`Var(High)`           | `470µF`
`Var(None,*)`         | `-! DNP`

\* This defines an Aspect Identifier _"Capacitance"_ including (at least, depending on the definitions used in other components) the Choice Identifiers _"Low"_, _"Medium"_, _"High"_, which define capacitance values, as well as _"None"_, which assigns the (capacitance) value `DNP` and also makes the component unfitted and excluded from position files and BoM.

> [!NOTE]
> In the above example, the Default Choice Identifier _"*"_ is added to the _"None"_ Choice, so that the corresponding expression also applies to any Choices declared outside this component in the same Aspect context. 
 Applying default data to Choices that the current component or assignment is "unaware" of may or may not be a good idea, depending on the chosen convenience vs. safety ratio.

<a name="cbe"></a>

##### Combined Base Expressions (CBE)

###### Typical Use

Using the [Base Scope](#base), **Combined Base Expression**s define the component's Value content, component attributes and features and/or the Aspect Identifier.

[Content](#content-specifiers) and [Property](#property-specifiers) specifiers are noted in the [Combined Format](#combined).

> [!NOTE]
> This Choice Expression type probably seems familiar, as it is very similar to the classic notation used in versions prior to 0.2.0 of KiVar.

###### Syntax

**Field name**: `Var`

**Field content:** `[<ASPECT_ID> ]<CIL_1>(<CAL_1>)[ <CIL_2>(<CAL_2>)[ ...[ <CIL_N>(<CAL_N>)]]]`

Used placeholders:
 * `<ASPECT_ID>` (optional) specifies the [Aspect Identifier](#aspect-identifier).
 * `<CIL_1>` .. `<CIL_N>` specify the [Choice Identifiers Lists](#choice-identifiers).
 * `<CAL_1>` .. `<CAL_N>` specify the corresponding [Choice Arguments Lists](#choice-arguments).

> [!NOTE]
> The [Aspect Identifier](#aspect-identifier) can be passed at _any_ element position within the Combined Expression (first or last position recommended for readability).

###### Examples

The following single entry serves the same purpose as the above [SBE](#sbe) example.  Note how even the [Aspect Identifier](#aspect-identifier) is included in the same single expression.

Field name     | Field content
-------------- | -------------
`Var`          | `Capacitance Low(10µF) Medium(100µF) High(470µF) None,*(-! DNP)`

The same explanation applies as for the above [SBE](#sbe) example.

<a name="sae"></a>

##### Simple Auxiliary Expressions (SAE)

###### Typical Use

Using the [Auxiliary Scope](#aux), **Simple Auxiliary Expression**s define the content of a specified _existing_ component field.

[Content](#content-specifiers) and [Property](#property-specifiers) specifiers are noted in the [Simple Format](#simple).

###### Syntax

**Field name**: `<TARGET_FIELD_NAME>.Var(<CIL>)`

**Field content:** `<CAL>`

Used placeholders:
 * `<TARGET_FIELD_NAME>` specifies the name of the component's field to assign specified content to.
 * `<CIL>` specifies the [Choice Identifiers List](#choice-identifiers).
 * `<CAL>` specifies the corresponding [Choice Arguments List](#choice-arguments).

###### Examples

The following entries could be used to define the MPN, description and datasheet URL for an imaginary LDO component.  Note that the target field names "Description", "MPN" and "Datasheet" must exist.

Field name                    | Field content
----------------------------- | -------------
`Description.Var(1.8V)`       | `Fixed voltage 1.8V 200mA LDO`
`Description.Var(3.3V)`       | `Fixed voltage 3.3V 200mA LDO`
`Description.Var(adjustable)` | `Adjustable voltage 200mA LDO`
`MPN.Var(1.8V)`               | `ALDO200V18`
`MPN.Var(3.3V)`               | `ALDO200V33`
`MPN.Var(adjustable)`         | `ALDO200ADJ`
`Datasheet.Var(1.8V,3.3V)`    | `"https://example.kivar.markh.de/products/aldo200v.pdf"`
`Datasheet.Var(adjustable)`   | `"https://example.kivar.markh.de/products/aldo200a.pdf"`

This defines the Choice Identifiers _"1.8V"_, _"3.3V"_ and _"adjustable"_, which define different field content for the target fields _"Description"_, _"MPN"_ and _"Datasheet"_.  Note how this example does not make use of the Default Choice Identifier _"*"_, as there are no sensible defaults that could be assigned for yet unknown Choices that may be declared by other components.

As it is not possible to _declare_ Choice Identifiers in the Auxiliary Scope (they rely on declarations in the [Base Scope](#base)), there must exist _at least_ the following Choice declarations in the same or another component that uses the same Aspect Identifier (_"Voltage"_ assumed here).  These Choice declarations are noted as [SBEs](#sbe), but Choices can be declared in any Expression Format (i.e. SBE or CBE types), even intermixed.

Field name                    | Field content
----------------------------- | -------------
`Var.Aspect`                  | `Voltage`
`Var(1.8V,3.3V,adjustable)`   | _(empty)_

<a name="cae"></a>

##### Combined Auxiliary Expressions (CAE)

###### Typical Use

Using the [Auxiliary Scope](#aux), **Combined Auxiliary Expression**s define the content of a specified _existing_ component field.

[Content](#content-specifiers) and [Property](#property-specifiers) specifiers are noted in the [Combined Format](#combined).

###### Syntax

**Field name**: `<TARGET_FIELD_NAME>.Var`

**Field content:** `<CIL_1>(<CAL_1>)[ <CIL_2>(<CAL_2>)[ ...[ <CIL_N>(<CAL_N>)]]]`

Used placeholders:
 * `<TARGET_FIELD_NAME>` specifies the name of the component's field to assign specified content to.
 * `<CIL_1>` .. `<CIL_N>` specify the [Choice Identifiers Lists](#choice-identifiers).
 * `<CAL_1>` .. `<CAL_N>` specify the corresponding [Choice Arguments Lists](#choice-arguments).

###### Examples

The following few entries serve the same purpose as the above [SAE](#sae) example.

Field name              | Field content
----------------------- | -------------
`Description.Var`       | `1.8V(Fixed voltage 1.8V 200mA LDO) 3.3V(Fixed voltage 3.3V 200mA LDO) adjustable(Adjustable voltage 200mA LDO)`
`MPN.Var`               | `1.8V(ALDO200V18) 3.3V(ALDO200V33) adjustable(ALDO200ADJ)`
`Datasheet.Var`         | `1.8V,3.3V("https://example.kivar.markh.de/products/aldo200v.pdf") adjustable("https://example.kivar.markh.de/products/aldo200a.pdf")`

The same explanation applies as for the above [CAE](#cae) example.

As explained above, _declaring_ Choice Identifiers is not allowed from the [Auxiliary Scope](#aux).  Hence, there must exist at least the following Choice declarations in the same or another component that uses the same Aspect Identifier.  These Choice declarations are noted as [CBCs](#cbe).

Field name             | Field content
---------------------- | -------------
`Var`                  | `Voltage 1.8V,3.3V,adjustable()`

#### Aspect Identifier

##### Purpose

To define to which aspect (i.e. group/dimension/degree of freedom) a component's Choice Identifiers relate to, an **Aspect Identifier** must be specified for every component that uses one or more Choice Expressions.

##### Specification

There are two methods of passing the **Aspect Identifier**:

1. Using the _dedicated component field_ `Var.Aspect`, or
2. as part of a [_Combined Base Expression_](#cbe).

Details and examples can be found in the following sections.

<a name="all-or-none"></a>

#### Fully Defined Assignments (The "All-or-None" Rule)

##### Purpose

One of the key concepts of KiVar requires all Configurations (sets of Choice selections) to be unambiguous with regard to their outcome.  This is required in order to be able to detect, i.e. map the assigned outcome back to an unambiguous set of Choices.

It is therefore required for **each Content or Property assignment** that there is
 * either **no definition** for **any** Choice involved (i.e. keep all Content or Property states in their original state)
 * or a **dedicated definition** for **every** Choice involved (i.e. set all Content or Property states to a defined state).

In short, assignments must be done for **either none or all** Choices.  There must be no sparsely defined assignments, because they would lead to inconsistent states when switching Choices.

> [!TIP]
> To avoid undefined assignments, Default Choices can be used.  For example, the Default Choice Identifier (`*`) can be added to the Choice Identifier List of an appropriate Choice Expression for that expression to also apply to otherwise undefined Choices.

> [!NOTE]
> The KiVar Choice Expression compiler will stop with an error if a sparse definitions are detected.

<!-- todo?
##### Content Scope

... TODO use default choice ...

##### Property Scope

... often no default required thanks to implicit defaults. if implicit defaults cannot be used, because different (+/-) states are assigned, explicit defaults must be used.
-->

#### Quoting and Escaping

**Special characters** inside a Choice Expression, such as `,` ` ` `-` `+` `(` `)` (comma, space, dash/minus, plus, parentheses) are **not** considered special (i.e. do not act as separators or Property Modifiers) if

 * they appear inside a quoted part of the definition, i.e. inside a matching pair of two unescaped `'` (single quotation mark) or `"` (double quotation mark) characters, or when
 * they are escaped, i.e. directly prepended with a `\` (backslash).

Single and double quotation mark characters (`'` and `"`) can be nested.  The inner quotation marks will be part of the verbatim string in this case.

To include any character as-is without being interpreted (e.g. `-` or `+` to be used as first character of a Content string, or a _quotation mark_ or _backslash_), that character must be _escaped_, i.e. preceded, with a _backslash_ character.

> [!TIP]
> For many cases, quoting and escaping in KiVar works just like in a regular POSIX shell interpreter.

> [!TIP]
> As long as they come in pairs and in the correct nesting order, parentheses (`(` and `)`) are not required to be escaped or quoted, as the expression parser can handle multiple levels of properly nested parentheses.  For example, `Choice_1(100nF (10%))` is fine, even without quoting or escaping.  Unusual arrangements, however, may require quoting or escaping in order to avoid misinterpretation by the parser.

_Examples:_

* To assign the fictional value `don't care` (a string containing a single quotation mark and a space), the appropriate Content Argument in the Choice Expression would be either `'don\'t care'` or `don\'t\ care`.
* To use `+5V` (a string starting with a plus) as a value, the choice definition arguments `'+5V'` or `\+5V` would be appropriate.  If the plus were not escaped, `+5V` would be interpreted as an (invalid) [Property Specifier](#property-specifiers).
* To assign an empty Content string (e.g. component value or target field content), use an empty quoted string (`''` or `""`) as [Content Specifier](#content-specifiers).
* To assign a list of simple words or values as Content (e.g. value specifications such as `47µF 35V 10% X7R`), the Content Specifiers can be naturally listed without quoting or escaping.
* To keep consecutive space characters, they must be escaped or quoted, e.g. to assign the Content string `three   spaces` the Content Specifier `three\ \ \ spaces`, `"three   spaces"` or `three'   'spaces` could be used.

> [!NOTE]
> The same quoting and escaping rules apply for Aspect and Choice Identifiers.

#### Expression Processing Example

The following figure illustrates the processing of some example Choice Expressions using [Combined Base Expressions](#cbe) (the classic Expression Type).

![Expression Processing Illustration](doc/processing.svg)

#### Real-World Examples

The following examples are taken from real commercial projects.  They show a few configurable variation aspects, their possible choices along with a short explanation of the implementation.

To further explore these examples and learn the recommended ways of implementing KiVar rules, check out the [demo project](demo/).

In the following sections, each example is illustrated with a schematic snippet including the values of the relevant fields for each related symbol.

##### Example 1: I²C Device Address Selection

In this very simple example, KiVar is used for address selection of an I²C device.  Address input A0 switches between device addresses 0x54 _(A0=GND)_ and 0x55 _(A0=+3V3)_.

![Example 1](doc/examples/1.svg)

The device address is selected by tying the IC input A0 to either GND or +3V3, depending on the selected choice.  Inputs A1 and A2 are tied to fixed levels.

How to read the rules:

 * Variation aspect is `EEPROM_ADDR` (with choice `0x55` currently applied in the figure).
 * **R1**: For choice `0x55` this part will be fitted (`+!`, resolving to `+fpb`).  There is no default choice required, as implicit defaults (opposite property states, i.e. `-fpb`) are assumed automatically.
 * **R2**: Likewise, for choice `0x54` this part will be fitted, else unfitted (same explanation as for R1).
 * **U1**: A purely informational field called `I2C Address` is assigned the value `0x54` or `0x55`, depending on the choice.  This field can then either be made visible directly, or referenced by other symbols or text boxes within the schematic (using text variable `${U1:I2C Address}`).

This example uses only classic [Combined Format](#combined) Expressions.

##### Example 2: Boot Source Selection

This is used for the boot source device selection for an NXP i.MX6ULL SoC.

![Example 2](doc/examples/2.svg)

The variation choices provide selection between the boot sources `EMMC`, `SD` and `NAND`, as well as an extra choice `JP` (which leaves _all_ configuration resistors unfitted, so that the user can configure the board by manually shorting the solder bridges JP1, JP2, JP3).

How to read the rules:

 * Variation aspect is `BOOT_SRC` (with choice `EMMC` currently applied in the figure).
 * **R9**: For choices `NAND` and `JP` this part is unfitted, else (`SD` and `EMMC`, handled by [Implicit Defaults](#implicit-defaults)) fitted.
 * **R10**: For choices `SD`, `EMMC` and `JP` this part is unfitted, else (`NAND`) fitted.
 * **R11**: For choices `SD`, `NAND` and `JP` this part is unfitted, else (`EMMC`) fitted.

> [!NOTE]
> The Aspect Identifier is specified in a dedicated field for each involved component, so that the (visible) Expressions can be kept short.  
> The Aspect Identifier field (`Var.Aspect`) is kept invisible, except for component R9, from where it is moved to the top of the figure for documentation purposes.  
> _Hint:_ In the Schematic Editor, uncheck the "Allow automatic placement" option for such moved fields.

This example uses only classic [Combined Format](#combined) Expressions.

##### Example 3: Undervoltage Trip Points

Typical use-cases for variations are resistor divider networks, such as voltage regulator feedback dividers or — in this case — a voltage divider with two taps for a programmable hysteresis on an undervoltage lock-out (UVLO) circuit.

![Example 3](doc/examples/3.svg)

The used variation aspect defines all four resistors (only two of them with varying values), allowing to select the lower (cut-off) and higher (recovery) voltage limits for the supply voltage monitor IC.

How to read the rules:

 * Variation aspect is `UVLO_HYST` (with choice `3.15V/3.57V` currently applied in the figure).
 * **R12**: For choice `2.41V/3.40V` the value is `0Ω`, for choice `3.15V/3.57V`, the value is `309kΩ`.
 * **R13**: The value is always set to `1MΩ`.  It is not really required to apply a value, or to use a variation rule at all for this symbol.  However, in case more choices are added in the future, it is very likely that the value of this resistor will change.  Hence the resistor symbol has the rule entry already prepared for easy introduction of new choices.
 * **R14**: For choice `2.41V/3.40V` the value is `309kΩ`, for choice `3.15V/3.57V`, the value is `100kΩ`.
 * **R15**: The value is always set to `750kΩ`.  Same explanation applies as for R13.

> [!NOTE]
> The Aspect Identifier is handled similarly to example 2 above.

##### Example 4: IC Variant Selection

This is used for selection of peripheral parts on a boost-buck-converter IC, which is available as _fixed_ (IRNZ suffix) and _adjustable_ (IRAZ suffix) voltage variants (just like many LDOs are, too).  Depending on the market availability of those IC variants, this variation aspect helps to quickly select between assembly options.

![Example 4](doc/examples/4.svg)

The fixed voltage IC variant requires direct feedback of the output voltage to the FB pin, while the adjustable voltage IC variant requires a typical feedback resistor network, including a capacitance of 66pF for stabilization.

How to read the rules:

 * Variation aspect is `ISL91127` (with choice `IRAZ` currently applied in the figure).
 * **C5**, **C6**: For choice `IRAZ` this part is fitted, else (`IRAZ`, handled by [Implicit Defaults](#implicit-defaults)) unfitted.
 * **R16**: For choice `IRAZ` the value is `1MΩ` (adjustable version using a voltage divider for feedback), for choice `IRNZ` the value is `0Ω` (fixed version using direct output voltage feedback).
 * **R17**: For choice `IRAZ` this part is fitted, else (`IRNZ`) it is unfitted.
 * **U3**: For choice `IRAZ`, set the component value to `ISL91127IRAZ`, for choice `IRNZ` set it to `ISL91127IRNZ`.  Also, set the `MPN` field accordingly (expression not shown in the schematic, check out the demo project).  
   Furthermore, for choice `IRAZ`, set the (visible) `Info` field content to `Adjustable`, for choice `IRNZ` set it to `Fixed` for documentation purposes.

> [!NOTE]
> The Aspect Identifier is referenced by a text field from component U3 using the text variable `${U3:Var.Aspect}`.  Using this technique, the pure Aspect Identifier can be placed inside any text for documentation purposes.

<!-- obsolete, U3 also mentions it... also this is fundamental knowledge and should not only be a side-note in the examples.
> [!NOTE]
> The Choice Expression in R16 is the _only_ one explicitly mentioning the Choice Identifier `IRNZ`, declaring that choice name for all rules that refer to the same Aspect Identifier (`ISL91127`).  
> You need at least one Choice Expression explicitly mentioning a Choice Identifier for it to be declared and available.
-->

##### Example 5: IC Type and Address Selection

This is used for selection of an I/O expander IC type (953**5** vs. 953**9**) along with its I²C address.  Different (footprint-compatible!) IC types interpret the input on pin 3 differently ("A2" vs. "/RESET").  See the text callout in the figure for details.

![Example 5](doc/examples/5.svg)

This example really implements two simple sub-aspects in a single variation aspect:
 * the type of the IC and
 * the device address.

As both sub-aspects depend on each other and can only be defined in a combined way, all sensible combinations (there are only three) must be defined for the combined aspect.  It is recommended to use the same dedicated sub-aspect separation character (`/` used in this example) in the Aspect Identifier as well as the Choice Identifiers to make it obvious to the user which sub-choice applies to which sub-aspect.

<!-- Add another example, which uses the classic technique (Infineon BTG PROFETs, for example)! Useful when the solder paste switch feature is implemented. As alternate, use 3D model switching and position offset switching (e.g. for JLCPCB).
In order to **switch the full set of ordering information or symbol and footprint library references** stored in the symbol fields, this example selects one of two alternate symbol instances, each using a slightly different symbol drawing (note the difference on pin 3).

In general, this variation technique can be used to switch between symbols that refer to either the same footprint (as in this example) or a different footprint shape (e.g. SMT vs. THT, or different SMT package sizes), which can exist side by side or even overlaid in the same spot of the PCB (only the footprints, _not_ the actual components!).

> [!TIP]
> Should you decide to use multiple overlapping footprint instances (of course, only one of them fitted with the actual component), the following custom DRC rule might become handy:
>
> ```
> (version 1)
>
> (rule "Allow overlapping courtyards for DNP parts"
>     (condition "A.Type == 'Footprint' && B.Type == 'Footprint' && A.Do_not_populate")
>     (constraint courtyard_clearance (min -1mm))
> )
> ```

> [!NOTE]
> If copper pads of multiple _alternate(!)_ footprints do overlap, it is important to assign the same net to each set of overlapping pads, in order to avoid DRC errors.  Some overlapping pads of alternate footprints will be applied the same net anyway (as in this example), but _unconnected_ symbol pins will automatically be applied calculated net names which will naturally conflict with those of alternate symbols if their corresponding copper pads overlap in the PCB.  It is then required to connect the unconnected pins with each other in the schematic (using wires or labels).  In the above example, visually distinguishable labels (P00..P17) were chosen for such connections that are otherwise without function.
-->

How to read the sub-aspects:

This example uses variation aspect `IOEXP_TYPE/ADDR` (read as: sub-aspects `IOEXP_TYPE` and `IOEXP_ADDR`) with choice `9539/0x74` (read as: `9539` selected for `IOEXP_TYPE`, `0x74` selected for `IOEXP_ADDR`) currently applied in the figure.

How to read the rules:

 * Variation aspect is `IOEXP_TYPE/ADDR` (see above).
 * **R18**: For choices `9535/0x24` and `9539/0x74` this part will be fitted, else (`9535/0x20`, handled by [Implicit Defaults](#implicit-defaults)) unfitted.
 * **R19**: For choice `9535/0x20` this part will be fitted, else (`9535/0x24`, `9539/0x74`) unfitted.
 * **U4**: The I²C address information field `I2C Address` is set according to the resulting address, depending on the selected choice.  Also, the `MPN` and `Datasheet` fields are set accordingly (expression not shown in the schematic, check out the demo project).

> [!NOTE]
> Depending on the available space in the schematic, the Aspect Identifier can be moved into the dedicated `Var.Aspect` field (and shown or hidden), as for U4, or be part of the Choice Expression, as for R18 and R19.

##### Example 6: Backlight LED Maximum Constant Current Selection

In this example a combination of resistor networks determines the maximum constant current for an LED backlight (_maximum_ because the used current regulator also has a PWM input, which can be controlled via software).

![Example 6](doc/examples/6.svg)

The resistor network combination allows to select an LED current from 10mA to 150mA in steps of 10mA.  Also, like in example 2, there is an additional choice `JP`, which leaves all four configuration resistors unfitted, so that the user can manually select the current using the solder bridges.

How to read the rules:

 * Variation aspect is `I_LED_MA` (with choice `100` currently applied in the figure).
 * **R21**: This is the _most significant_ path for 80mA current. For the upper half of the current choices, i.e. `80` up to `150`, the resistor is fitted.  For other choices (incl. `JP`) the part is unfitted (handled by [Implicit Defaults](#implicit-defaults)).
 * **R22**: This is the path for 40mA current. For choices `40` through `70` and `120` through `150` the resistor is fitted.  For other choices (incl. `JP`) it is unfitted.
 * **R29**: This is the path for 20mA current. For choices `20`, `30`, `60`, `70`, `100`, `110`, `140`, `150` the resistor is fitted.  For other choices (incl. `JP`) it is unfitted.
 * **R30**: This is the _least significant_ path for 10mA current. For choices `10`, `30`, `50`, `70`, `90`, `110`, `130`, `150` the resistor is fitted.  For other choices (incl. `JP`) it is unfitted.

> [!NOTE]
> Again, to save horizontal space, the Aspect Identifier is moved to the dedicated `Var.Aspect` field (shown), for all involved components.

### Rules Application

After setting up the rules for each relevant symbol (or footprint), variations can finally be switched using the _KiVar_ plugin or CLI app.

#### Using the KiVar Action Plugin

##### Update the PCB

If the expressions were set up in the Schematic Editor (eeschema), they need to be updated to the PCB Editor first (menu item _Tools &rarr; Update PCB from Schematic..._).

##### Run the Plugin

To open the plugin dialog, simply click the KiVar plugin icon in the main toolbar, or choose the _KiVar_ menu item under _Tools &rarr; External Plugins_.

##### Configuration Identification

Upon start, during the compilation stage, KiVar automatically detects the current variation configuration, i.e., it tries to find a definite choice for each configured aspect, based on the currently assigned values, field contents and attributes for each related footprint.

If they do not exactly match one definite choice (per variation aspect), then the corresponding variation choice selector is preset to the entry _'\<unset>'_.  This will probably happen before applying a specific choice for the first time or after editing expressions, because not all of the currently assigned footprint properties may perfectly match one of the defined variation choices.

##### Possible Error Messages

In case the defined choice expressions cannot be parsed and/or compiled without problems, an error message window with a list of problems is presented.  Each of the listed problems must then be fixed in order to successfully start the plugin.

> [!TIP]
> Error messages can be clicked to focus the corresponding footprint on the _pcbnew_ canvas in the background.

##### Variation Choices Selection

If all expressions can be compiled without problems, the plugin dialog window appears.

For the above [real-world examples](#real-world-examples), the selection dialog window may look similar to the following:

![Variant Selection Dialog Without Changes](doc/plugin-empty.svg)

For each of the listed Aspect Identifiers a variation Choice Identifier can now be selected.

If the values, field contents and attributes of the footprint(s) related to a variation aspect shall not be modified, the entry _'\<unset>'_ can be selected for that variation aspect.  In this case, the corresponding variation will be excluded from the assignment stage and related footprints remain unmodified.

The change list section below the selection area summarizes all component changes to be performed for each related footprint if the current variation configuration is applied.

> [!TIP]
> Entries in the change list can be clicked to focus the corresponding footprint on the _pcbnew_ canvas in the background.

After selecting a few different variation choices, the dialog window may look like the following:

![Variant Selection Dialog With Changes](doc/plugin-changes.svg)

When clicking the _Update PCB_ button, KiVar sets the values and attributes for all relevant footprints as previewed in the information text box.

##### Visible Changes

The performed changes will immediately be visible in the PCB Editor (e.g. for shown footprint values) and the 3D Viewer window (immediately or after refresh, depending on the preferences setting).

The following images show the 3D board view for the original settings:

![3D Board View Without Changes](doc/pcb-nochange.png)

... and after applying the new variation configuration (according to the dialog window above):

![3D Board View With Changes](doc/pcb-change.png)

##### Updating the Schematic

All changes by the plugin are only performed in the board, as KiVar is a plugin for _pcbnew_ (_eeschema_ does not yet have a plugin interface).  That is, the performed changes must be propagated back from the board to the schematic in order to be visible there (e.g. for changed values and DNP markings).

To propagate the changes back to the schematic, use the PCB Editor menu item _Tools &rarr; Update Schematic from PCB..._ and make sure to select the checkboxes _Values_ and _Attributes_\*.  If you have modified the KiVar rules inside the PCB Editor, i.e. edited the footprint fields\* instead of the symbol fields, then also select the checkbox _Other fields_\*, in order to propagate your KiVar rules to the schematic.

#### Using the KiVar Command Line Application

The KiVar CLI application works similar to the plugin, except that it manipulates an existing `.kicad_pcb` file (which must not be opened in another application).

For usage information and available commands and options, run:

```
kivar --help
```

<a name="migrate"></a>

## Migrating from Earlier KiVar Versions

### Migrating from KiVar 0.1.x to 0.2.x

KiVar 0.2.0 introduced changes and enhancements to the rule syntax.  The following sub-sections will support experienced users of KiVar 0.1.x with updating their legacy variation rules for current and upcoming KiVar versions.

#### New Field Names

Severity: **Critical**.

While KiVar 0.1.x and earlier used a single field named `KiVar.Rule`, current releases use the field `Var` for quite the same purpose.

So as a first step users should move all legacy rules from `KiVar.Rule` to `Var`.  This can be achieved by copying and pasting the values of the `KiVar.Rule` column over to the `Var` column in the KiCad Schematic Editor's Symbol Fields Table.

> [!TIP]
> To do this, open the Symbol Fields Table, sort by the legacy `KiVar.Rule` field, then copy & paste all relevant cells to the `Var` field (which may need to be created first).  Afterwards, remove all `KiVar.Rule` fields (can be done in the Symbol Fields Table dialog).

Further reading: [Choice Expressions](#choice-expressions).

#### Basic Rule Format

While the legacy format of the `KiVar.Rule` field is very similar to the current "[Combined Base Expression Type](#cbe)" (using the `Var` field), there have been some changes that may (or may not) break existing legacy rules.  Users will need to revise their legacy rules to be sure that they are parsed as expected with current (and upcoming) versions of KiVar.

The following sections will cover the details.

#### Property (Formerly Options) Inheritance

Severity: **Critical**.

Prior to version 0.2.0, KiVar supported "Option" arguments.  An Option always started with a `-` (dash) character, followed by the Option identifier.  The only supported Option identifier was `!`, which resulted in the _Do not populate_, _Exclude from Position Files_ and _Exclude from BoM_ component attributes to be set (or cleared if the option was _not_ provided!).

<!-- An Option could either be specified or _not_ specified.  There was no way of "overriding" an Option that was set via inheritance from a default Choice. -->

If an Option was specified in a [Default Choice](#default-choices) (specified by the Choice Identifier `*`), that Option was **not inherited** by specific Choice Expressions, but would have to be specified again in all specific expression in order to be effective for those choices.

This (questionable) design decision had been made because there was no way to reset an Option specified in a Default Choice when overriding that Default Choice with a specific Choice.  Hence, every Choice declaration/definition caused all Options to be reset for that specific Choice, to allow for providing a fresh set of Options for specific Choices.

Values, however, were handled differently: They _were_ inherited from the Default choice definition and used as long as no Value was passed in a specific rule.

With version 0.2.0, this behavior has changed.  Default Choice inheritance has been streamlined and now applies to both Values (now called _Content_) and Options (now called _Properties_), thanks to the introduction of enhanced [Property Specifiers](#property-specifiers).  _Property Modifiers_ now allow overriding property states with either _set_ (modifier `+`) or _clear_ (modifier `-`) operations.  That is, after the Default Property states are applied (inherited), specific choices can (partially) override those states.

There are now three supported effective Properties:
 * **Fitted** (identifier `f`): Component is fitted.  Clears the "Do not populate" component attribute.
 * **inPos** (identifier `p`): Component is listed in Position files.  Clears the "Exclude from Position Files" component attribute.
 * **inBom** (identifier `b`): Component is listed in Bill of Materials.  Clears the "Exclude from BoM" component attribute.

There is also a [Group Property](#group-properties) `!`, which resolves to "Fitted", "InPos" and "InBom", being _nearly_ backwards-compatible to the old `-!` Option.  However, **special care must be taken when `-!` appears in Default choices, as those Properties are now inherited by specific choices**.

The following examples try to illustrate the different handling:

_**Old** behavior:_

Rule String           | Resulting Choice1 Value | Resulting Choice1 Options | Resulting Choice2 Value | Resulting Choice2 Options |
--------------------- | ----------------------- | ------------------------- | ----------------------- | ------------------------- |
`*(10k -!) Choice2()` | `10k`                   | `-!`                      | `10k` (inheritance)     | _(none)_ (no inheritance) |

_**New** behavior:_

Rule String             | Resulting Choice1 Content | Resulting Choice1 Properties  | Resulting Choice2 Content | Resulting Choice2 Properties
----------------------- | ------------------------- | ----------------------------- | ------------------------- | --------------------------------
`*(10k -!) Choice2()`   | `10k`                     | `-!` (effectively `-f -b -p`) | `10k`                     | `-!` (effectively `-f -b -p`)
`*(10k -!) Choice2(+b)` | `10k`                     | `-!` (effectively `-f -b -p`) | `10k`                     | `-! +b` (effectively `-f +b -p`)

> [!IMPORTANT]
> Component attributes (DNP, Not in Pos, Not in BoM) are now **kept at their current state** (and ignored in the Choice match) if their corresponding properties are **not defined** (to _true_ or _false_).  
> In versions prior to 0.2.0 all three component attributes were either set or cleared, depending on the presence of the `-!` option.  They could not be set to different states, and none of them could be kept untouched for component with variation rules.  Version 0.2.0 introduces much more flexibility regarding attribute management.

Further reading: [Default Choices](#default-choices).

#### Implicit Property Default States

Severity: **Not critical** (backwards-compatible).

Starting with version 0.2.0, users can choose to _only_ specify the Property State that makes a Choice unique and let the the KiVar rule compiler assume the opposite state to be the [_Implicit_ Default](#implicit-defaults) state (if no default Property State is provided otherwise) for other choices of the same assignment.

For example, if a component is only fitted (Property Identifier `f`) in one Choice (of many), it is now sufficient to specify `+f` in _that_ Choice Expression and leave the rest of the assignment choices and the [Default Choice](#default-choices) (`*`) without a definition for the `f` Property.  The implicit default state for the `f` (fitted) Property will then automatically assumed to be the opposite (`-f`) for any other Choices.

> [!IMPORTANT]
> Implicit Property States can only be used if there is only **one** type of State/Polarity (either `+` or `-`) assigned in any of the assignment's choices.

> [!IMPORTANT]
> Implicit default States only work for Property States, as they use _boolean_ states (actually tri-state, but as soon as a Property is provided, it's either _true_ or _false_) and therefore have an (implicit) "opposite" value.

Further reading: [Implicit Defaults](#implicit-defaults).

#### Values As Multiple Words

Severity: **Not critical** (backwards-compatible).

Prior to version 0.2.0 multiple Value arguments were forbidden inside a Choice Expression.  Only a single Value argument was allowed to be assigned to a Choice definition.  In case of multiple "words", the argument had to be quoted (with `'` (single-quote) characters) in order to be accepted as a single argument.

Starting with version 0.2.0, Choice Expressions can now contain multiple Value (now called _Content_) arguments, which are joined with a single ` ` (space) character inbetween.

This change is fully backwards-compatible.  There is no need to adapt legacy rule strings.

Further reading: [Content Specifiers](#content-specifiers).

#### Aspect Identifier Position

Severity: **Not critical** (backwards-compatible).

Before version 0.2.0 the aspect identifier (name) had to be the first argument in every rule string.  From version 0.2.0 on, the aspect identifier can be specified at any position, or even left away and instead be specified in a different component field (`Var.Aspect`).

This change is fully backwards-compatible.  There is no need to adapt legacy rule strings.

Further reading: [Aspect Identifier](#aspect-identifier).

#### New Choice Expression Types and Formats

Severity: **Not critical** (backwards-compatible).

Versions before 0.2.0 supported only a single rule format in the `KiVar.Rule` component field.  From version 0.2.0 on, multiple rule (now called _Choice Expression_) formats are supported, which can be specified in different component fields.

This change is fully backwards-compatible.  Apart from the changes discussed above, there is no need to change the format of legacy rule strings.

Further reading: [Choice Expressions](#choice-expressions).

#### Double-Quote Characters Support

Severity: **Not critical** (backwards-compatible).

Prior to version 0.2.0 only `'` (single-quote) characters could be used for the purpose of quoting verbatim strings.

Starting with version 0.2.0, `"` (double-quote) characters are also supported for quoting.  Single- and double-quote strings can be nested, e.g. the string `"hello 'world'"` would result in `hello 'world'`.

This change is mostly backwards-compatible.  If your legacy string do not use double-quote characters that are supposed to be used in a verbatim fashion themselves, there is no need to adapt legacy rule strings.

Further reading: [Quoting and Escaping](#quoting-and-escaping).

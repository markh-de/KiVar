# KiVar − PCB Assembly Variants for KiCad

## Introduction

<img align='right' width='92' src='doc/kivar-icon.inkscape.svg'>

KiVar is a tool for **KiCad PCB Assembly Variant selection**, available as

 * **KiCad Action Plugin** and
 * **Command Line Application** (Python).

PCB component variation rules are defined in component (i.e. symbol or footprint) fields.  This allows for the complete variant configuration to be contained in the schematic and board files without requiring external data from outside the native KiCad design files.

The name _KiVar_ (for _KiCad Variants_, obviously) can also be read as an acronym for _**Ki**Cad **V**ariation **a**ssignment **r**ules_.

## Features

KiVar assigns PCB component **values** and **attributes** (such as _Do not populate_, _Not in position files_, _Not in BoM_) according to variation rules specified in footprint fields.  When applying those rules, component values and attributes are modified _in place_, allowing for immediate update of the PCB design as well as the 3D view and enabling compatibility with _any_ exporter.

Back-propagation of modified component data from the PCB to the schematic can be done in an extra step.

**TODO** Add screenshot of plugin (same as below?), add screenshot of CLI app.

## Concepts

Key concepts of KiVar are:

 * A single design may use **multiple** independent variation **aspects** (i.e. dimensions or degrees of freedom).
 * Variation rules are **fully contained** in component fields of native design files (no external configuration files) and **portable** (i.e. copying components to another design keeps their variation specification intact).
 * Component values and attributes are modified **in place**, enabling compatibility with all exporters that work on the actual component data.
 * **No external state information** is stored, i.e. all currently selected/matching variation choices are detected automatically.

## Supported KiCad Versions

KiVar releases 0.2.0 and later require at least **KiCad release 8**.

Earlier versions of KiVar also supported KiCad 7, but in a very restricted way.  Hence, after the release of KiCad 8, KiVar support for KiCad 7 was dropped.

## Installation

### KiVar Action Plugin

The KiVar Action Plugin uses the Python API wrapper for pcbnew, the KiCad PCB Editor.

The recommended installation method is to use KiCad's integrated **Plugin and Content Manager**.  KiVar is included in the official PCM repository, allowing a smooth and safe installation experience.  For manual installation users can also choose to download the plugin archive packages.

#### Using the Plugin and Content Manager

Required steps:

1. Start the _Plugin and Content Manager_ from the KiCad main window.
2. Find _KiVar_ in the **Plugins** section.
3. Mark it for installation and apply the pending changes.
4. The _Kivar_ plugin icon should now appear in the PCB Editor (pcbnew) toolbar.

#### Using Manual Archive Extraction

Required steps:

1. Open the KiCad PCB Editor (pcbnew).
2. In the PCB Editor, choose the menu option _Tools &rarr; External Plugins &rarr; Open Plugin Directory_.  This will open a file browser at the location of your KiCad plugin directory.
3. Unzip the contents of an official [KiVar release archive](https://github.com/markh-de/KiVar/releases) (the ZIP file _without_ the `-pcm` suffix) to that KiCad plugin directory you opened in the previous step.  _Important:_ Do not create another directory inside the target plugin directory, but only place the files from the release archive directly in the plugin directory.
4. Switch back to the PCB Editor and choose the menu option _Tools &rarr; External Plugins &rarr; Refresh Plugins_.  The _KiVar_ plugin icon should now appear in the toolbar and in the plugin list under _Tools &rarr; External Plugins_.

If the installation does not work for you this way, consider reporting your problem as an issue in the KiVar bug tracker.

### KiVar Command Line Application

#### Using PyPI

To install the KiVar CLI using the official PyPI repository, open a shell and run:

```
pip install kivar
```

**TODO**

## Usage

The process of writing and assigning rules to components (i.e. symbols and footprints) is done manually using simple expressions.

Once all relevant components are equipped with their variation rules, KiVar allows the selection of variation choices using either an easy-to-use dialog interface (when using the Action Plugin) or a command-line interface (when using the CLI application) and takes care of the automatic analysis and assignment of the corresponding component values, fields and attributes.

The following sections describe the process of configuring your schematic or board and - after that - selecting a variation configuration from the previously configured variation choices.

### Component Variation Setup

The following sub-sections describe the variation rules setup procedure.

While it is recommended to define variation rules in the schematic (i.e. in symbol fields) and propagate them to the board, it is also possible to define those rules directly in the board (i.e. in footprint fields) and propagate them back to the schematic.  Either way, in the end the rules must be present in the footprint fields, as KiVar uses the _pcbnew_ API wrapper and can therefore only operate on board (not schematic) data, which must then be propagated back to the schematic as described in later sections. (TODO link)

#### Migrating from KiVar 0.1.x

KiVar 0.2.0 introduced changes and enhancements to the rule syntax.  The following sub-sections will support experienced users of KiVar 0.1.x with updating their legacy variation rules for current and upcoming KiVar releases.

##### New Field Names

While KiVar 0.1.x and earlier used a single field `KiVar.Rule`, current releases use `Var` for quite the same purpose.

So as a first step you should move all legacy rules from `KiVar.Rule` to `Var`.  This can be achieved simply with copy & paste in the KiCad Schematic Editor's Symbol Fields Table.

_Hint:_  In the Symbol Fields Table, sort by the legacy `KiVar.Rule` field, then copy & paste all relevant cells to the `Var` field.  Afterwards, remove all `KiVar.Rule` fields (can be done in the Symbol Fields Table dialog).

##### Basic Rule Format

While the legacy rule format of the `KiVar.Rule` field is very similar to the current `Var` field expression format, there have been some changes that may (or may not) break your legacy rules.  You will need to review your legacy rules to be sure that they are parsed correctly with current (and upcoming) versions of KiVar.

The following sections will cover the details.

##### Property (Formerly Options) Inheritance

Severity: Critical.

***TODO*** add examples old -> new

##### Implicit Default Properties

Severity: Critical.

While being party backwards-compatible, the `-!` statement is now no longer an option, but a property modifier.

***TODO***

##### Values As Multiple Words

Severity: Not critical (relaxed rules).

***TODO***

##### Aspect Identifier Position

Severity: Not critical (relaxed rules).

***TODO***

##### New Choice Expression Types and Formats

Severity: Not critical (optional enhancements).

***TODO***

#### Definition of Terms

As mentioned before, KiVar supports multiple independent _variation aspects_ per board.  For each of these variation aspects, one _variation choice_ can be made later during the selection process.  The result of selecting a specific set of choices for a given set of aspects forms a _variation configuration_.

Basic terms used in this document:

 * **Aspect:**  
   A dimension of variation changes, which are defined by _Choices_ (see below).  One PCB design can refer to multiple aspects.  Each component, which makes use of KiVar variations, must refer to exactly one aspect identifier.
 
 * **Choice:**  
   A set of values (component values or field contents) and/or properties to be assigned to specific components.  A Choice is always related to a specific _Aspect_.

 * **Configuration:**  
   A fully defined set of specific _Choices_ for _all_ available _Aspects_.  In other words, one specific board assembly variant state.

#### Basic Rules Structure

Each component (which uses KiVar variation rules) must refer to exactly one **Aspect**.  The **Choices** defined or referred to in the component are always related to that Aspect.

There can exist multiple Aspects per design, and for each Aspect there can exist multiple Choices.

Example:

 * Aspect `DEV_ADDR`
   * Choice `0x50`
   * Choice `0x51`
   * Choice `0x52`

 * Aspect `BOOT_SRC`
   * Choice `EMMC`
   * Choice `SDCARD`
   * Choice `NAND`

 * Aspect `VIO_LEVEL`
   * Choice `1.8V`
   * Choice `2.5V`
   * Choice `3.3V`

One possible example _Configuration_ for these Aspects and Choices:

`DEV_ADDR=0x52 BOOT_SRC=NAND VIO_LEVEL=1.8V`

KiVar computes such sets of Aspect and Choice definitions internally by checking each component's field data for KiVar _Choice Expressions_, which are explained in the following sections.

#### Choice Expressions

Component variation rules are specified in **Choice Expression**s (short: _CE_), which are defined in the fields of each component (i.e. symbol and/or footprint) they relate to.  Multiple components may (and usually will) refer to the same aspects and choices.

One component must relate to a single aspect, but can relate to an unlimited number of choices for that aspect.

Choice expressions can be noted in various formats, which are described in the following sections from their innermost to the outermost elements.

#### Choice Arguments

In its simplest form, a Choice Expression consists only of a **Choice Argument List** (short: _CAL_), which is just a list of _space_-separated **Choice Argument**s (short: _CA_) to be assigned to a component for a specific choice.

Each _Choice Argument_ of the _Choice Argument List_ can be of one of two possible types:
 * a part of the **content** to be assigned as the component _value_ or a specific _field_ or
 * a **property** assignment specifier (to mark a component _(un)fitted_, _(not) in BoM_, _(not) in position files_).

Argument types are distinguished by their first (unescaped) character and will be explained in more detail in the followin sub-sections.

##### Content Choice Arguments

Each argument beginning with a character _other than_ `-` and `+` is classified as part of the content.  Such arguments are concatenated with a single space character between each argument.

_Note:_ As arguments can be separated by any number of _space_ characters, each separation using multiple spaces will result in a single space character in the final content.  For strings that shall be assigned in a verbatim way (such as a URL), it is highly recommended to use quoting techniques (discussed later).

Examples:

The following input Choice Argument Lists will result in the following content strings (other resulting data ignored for now):

Choice Argument List input | Resulting content string | Explanation
-------------------------- | ------------------------ | -----------
`100nF`                    | `100nF`                  | Simple single arguments can be noted without escaping or quoting as long as they don't contain certain special characters (discussed later).
`470µF 10%`                | `470µF 10%`              | Uncritical text, no verbatim adoption of the arguments required.
`470µF   10%`              | `470µF 10%`              | Multiple separator characters will be converted to a single separator. As the text is uncritical, this conversion may even be desired.
`'https://kivar.markh.de/datasheet/abc123.pdf'` | `https://kivar.markh.de/datasheet/abc123.pdf` | Strings to be used verbatim should always be enclosed in quote characters.
`'abc   def ' 123   456`   | `abc   def  123 456`     | Mixed type of quoted and unquoted representation.  Note how the trailing space after `def` remains contained in the result.
`abc +p -b def`            | `abc def`                | (TODO) Properties are discussed below.
`abc \+p '-b' def`         | `abc def`                | (TODO) Properties are discussed below.
`abc "def 'ghi' jkl" mno`  | ...

##### Property Choice Arguments

(TODO)

##### Examples

The following table provides some examples along with their results when applied and explanations for each case.

CAL            | Resulting content | Resulting property states | Explanation
---|---|---|---
`a list of words` | `a list of words` | | The content results in all arguments joined with a space character.
`just   like in   html` | `just like in html` | | Similar, but note that multiple separation spaces in the CAL result in a single space in the content.
`This is ' a  verbatim string'` | `This is  a  verbatim string` | | In quoted parts, spaces (and other special characters) are preserved.
(TODO) more, with quoted prop specs ...

(TODO) table with examples of CALs, resulting content and properties, along with explanation

#### Choice Identifiers

(TODO) as part of CIL

##### Examples

(TODO) multiple components, to illustrate default choice behavior

(TODO) following sections one heading level up

##### Choice Expression Scopes

There are two basic scopes of Choice Expressions:

1. **Base Choice Expressions** (BCE)
   * assign component **values** and **properties** while they
   * _define_ or _extend_ the set of available choices for a given aspect.

2. **Auxiliary Choice Expressions** (ACE)
   * assign values to specific custom **fields** (other than the _Value_ field) while they
   * _refer to_ already defined aspect choices.

##### Choice Expression Formats

Furthermore, Choice Expressions can be defined in different ways, depending on the user's preferences and requirements.  There are two different Choice Expression formats:

1. **Simple Choice Expressions** (SCE)
   * specify a single Choice Expression using
   * one specific component field per expression.

2. **Combined Choice Expressions** (CCE)
   * allow combining multiple Choice Expressions in a
   * single component field (also, for Base Choice Expressions, optionally accepting the Aspect identifier).

##### Choice Expression Types

The combination of both expression scopes and both expression formats allow for the following four Choice Expression types:

1. **Simple Base Choice Expressions** (SBCE)  
   use the field `Var(<CHOICELIST>)` with field content in [SCE](#SCE) format to assign component value and properties to a specific choice list `<CHOICELIST>`.

2. **Combined Base Choice Expressions** (CBCE)  
   use the field `Var` with field content in [CCE](#CCE) format (with an Aspect identifier allowed) to assign component values and properties to one or more choice lists.

3. **Simple Auxiliary Choice Expressions** (SACE)  
   use the field `<CUSTOMFIELD>.Var(<CHOICELIST>)` with field content in [SCE](#SCE) format to assign a specific value for the component's custom field `<CUSTOMFIELD>` to a specific choice list `<CHOICELIST>`.

4. **Combined Auxiliary Choice Expressions** (CACE)  
   use the field `<CUSTOMFIELD>.Var` with field content in [CCE](#CCE) format (with no Aspect identifier allowed) to assign values for the component's custom field `<CUSTOMFIELD>` to one or more choice lists.

##### Aspect Identifier Specification

As mentioned above, each component that provides KiVar variation rules must refer to exactly one Aspect.

There are two methods of passing the **Aspect identifier**:

1. Using the _dedicated component field_ `Var.Aspect`, or
2. as part of a _Combined Base Choice Expression_.

Details and examples can be found in the following sections.

#### Definition Syntax

As mentioned above, Choice Expressions can be specified in various ways to cover most user requirements.

The following sub-sections explain how and when to use which Choice Expression types.  Although the basic syntax rules are covered in later sections, examples are used below for illustrative purposes.

##### Example use-case

For the upcoming sections, assume the following hypothetical use-case:

KiVar shall allow switching between two IC types for component _U1_.  For this the following two choices are declared:
 * `9535` (for IC type _TCA953**5**PWR_) and
 * `9539` (for IC type _TCA953**9**PWR_).

Both ICs are I²C port expanders that are mostly pin-compatible.  Provided the schematic is designed correctly, both ICs are interchangeable without any changes to the PCB layout.

As KiVar allows multiple aspects, the above choices must be assigned to an aspect, forming a group for both choices.  The aspect identifier for the above choices shall be `IOEXP_TYPE`.

The following field content assignments shall be performed by KiVar for each choice:

Field Name    | Content for Choice `9535`                      | Content for Choice `9539`
--------------|------------------------------------------------|--------------------------
`Value`       | `TCA9535PWR`                                   | `TCA9539PWR`
`MPN`         | `TCA9535PWR`                                   | `TCA9539PWR`
`I2C Address` | `0x20`                                         | `0x74`
`Datasheet`   | `https://www.ti.com/lit/ds/symlink/tca9535.pdf` | `https://www.ti.com/lit/ds/symlink/tca9539.pdf`

##### Simple Choice Expression (SCE)

SCEs specify a single Choice Expression per component field.  In a typical use-case, multiple such expressions will be used to describe multiple values, properties or field contents of the corresponding component.  They can be mixed with CCE (see below) to form a complete set of Choice Expressions.

As described above, SCEs can be used for Base and Auxiliary CEs (as SBCE and SACE).

According to our example use-case, the _Value_ field of component _U1_ shall be changed.  For this we need Simple _Base_ Choice Expressions (SBCE), which allow declaring and defining choices and the component values (and properties) associated with them.  For component _U1_ we add the following data:

Field Name  | Field Content
------------|--------------
`Var(9535)` | `TCA9535PWR`
`Var(9539)` | `TCA9539PWR`

As SCEs do not allow specifying the aspect identifier, we need to add an additional field to specify the aspect to which the above choices apply:

Field Name   | Field Content
-------------|--------------
`Var.Aspect` | `IOEXP_TYPE`

Now that we have declared and defined the choices `9535` and `9539` for aspect `IOEXP_TYPE`, we can refer to them in Auxiliary expressions, which are used for defining _custom field_ contents (i.e. fields other than the component's _Value_ field).  So to assign data to the _MPN_ field, depending on the selected choice, we now use Simple Auxiliary Choice Expressions (SACE):

Field Name      | Field Content
----------------|--------------
`MPN.Var(9535)` | `TCA9535PWR`
`MPN.Var(9539)` | `TCA9539PWR`

Depending on the selected choice, the effective I²C address should be assigned to a custom component field, for information purposes only.  That information can later be added to the schematic symbol instance to be visible in the schematic.  This is very helpful when checking for potential address conflicts. 
 The address assignment can be done with these additional Auxiliary expressions:

Field Name              | Field Content
------------------------|--------------
`I2C Address.Var(9535)` | `0x20`
`I2C Address.Var(9535)` | `0x74`

While SCEs can also be used to assign such short and simple field contents, they are much better suited for longer contents that would make a CCE (see below) too long or too complicated, such as the datasheet URL in the following Auxiliary expressions:

Field Name            | Field Content
----------------------|--------------
`Datasheet.Var(9535)` | `https://www.ti.com/lit/ds/symlink/tca9535.pdf`
`Datasheet.Var(9539)` | `https://www.ti.com/lit/ds/symlink/tca9539.pdf`

##### Combined Choice Expressions (CCE)

CCEs allow specifying multiple Choice Expressions per component field, even along the aspect identifier (for Base expressions).  CCEs enable much more compact expressions.

The above expressions can be implemented in a much more compact fashion when using CCEs instead.  For component _U1_, the following rules would have the same effect as the above SCEs and fulfill our example use-case:

Field Name        | Field Content
------------------|--------------
`Var`             | `9535(TCA9535PWR) 9539(TCA9539PWR) IOEXP_TYPE`
`MPN.Var`         | `9535(TCA9535PWR) 9539(TCA9539PWR)`
`I2C Address.Var` | `9535(0x20) 9539(0x74)`
`Datasheet.Var`   | `9535('https://www.ti.com/lit/ds/symlink/tca9535.pdf') 9539('https://www.ti.com/lit/ds/symlink/tca9539.pdf')`

Note how the aspect identifier is passed inside the CBCE (field `Var`).  Inside a CBCE KiVar recognizes the aspect identifier by the missing round brackets.

Another benefit of using CCEs is that the variety of different field names used in your schematic is kept low, because the different choice names are not part of the field name.  If there are many different field names, the Symbol Fields Table in the schematic editor can become quite cluttered.

However, for assignments containing very long or complex strings (such as URLs), SBEs may be a better choice.

Also note the usage of string quoting (discussed later) around the URLs.  Although it is not strictly required in this example, it is good practice to quote complex strings that may contain special characters that could be recognized by the parser.

As noted above, SBEs and CBEs can be mixed.



(TODO move this)
_Hint:_ It is recommended to add `Var` and **TODO** as project field name templates (configured under _File &rarr; Schematic Setup... &rarr; General &rarr; Field Name Templates_), so that rules can easily be created without manually adding those fields and their names for each affected symbol.






The following figure summarizes the structure of a rule definition.  Each part of it is explained in more detail in the following sections. 

***TODO*** new example, more specific aspect and choice names. LED color (red/green/yellow/white) and matching resistors? optionally changing the LED MPN?

![Variation Definition Composition](doc/rule.png)

For the upcoming sections, the following simple example rules are used for illustration purposes (components `R1` and `R2`):

 * `R1`: `KiVar.Rule` = `ASPECT_A CHOICE_1(0Ω) CHOICE_2,CHOICE_3(10kΩ)`
 * `R2`: `KiVar.Rule` = `ASPECT_A CHOICE_3() *(-!)`

##### Rule Definition

A **rule definition** consists of multiple sections, separated by one or more (unescaped) _space_ characters.

The **first** section of each rule definition contains the **aspect name**.

**Any subsequent** sections contain **choice definitions**, which relate to the aspect name specified in the first section.

Looking at `R1` of the illustration example, `ASPECT_A` is the aspect name, and the choice definitions _for that aspect_ are defined as:

 * `CHOICE_1(0Ω)` and
 * `CHOICE_2,CHOICE_3(10kΩ)`

Follow the next sections for further explanations.

##### Choice Definition

A choice definition consists of two parts: One or more **choice names** (_comma_-separated), directly followed by a pair of parentheses containing the **choice arguments**.

The _choice names_ declare to which variation choices the given choice arguments shall be applied.

The _choice arguments_ contain any number of arguments (separated by unescaped _space_ characters) to be applied to each listed choice name.

For the illustration example the following assignments apply:

**R1** creates `ASPECT_A` with:

 * the new choice `CHOICE_1` with argument `0Ω`,
 * the new choices `CHOICE_2` and `CHOICE_3` with argument `10kΩ`, each.

**R2** enhances `ASPECT_A` with:

 * the already known `CHOICE_3` without arguments,
 * the default choice `*` (i.e. applies to `CHOICE_1` and `CHOICE_2`, see below) with argument `-!`.

##### Choice Definition Arguments

Each choice definition may contain the following choice argument types:

 * a **value** (one at most) to be assigned to the footprint's value field when that choice is selected during the variation choice selection process, and
 * **options** (none or more) to be assigned to the applicable choice(s).

_Important:_ All arguments starting with an _unescaped_ `-` (dash) character are considered **options**.  Any other arguments are considered **values**.

For the illustration example this means that the arguments `0Ω` and `10kΩ` are considered component values, while `-!` is considered an option.

##### Supported Options

Currently only one type of option is supported:

`!` — **Unfit component**.  If specified, sets the following attributes for the related footprint:

  * _Do not populate_ (not yet supported in KiCad 7),
  * _Exclude from position files_,
  * _Exclude from Bill of Materials_.

If this option is _not_ provided for a specific choice, then the above attributes will be _cleared_ for that choice, i.e. the part will be "fitted" and hence marked as populated and included in position files and BoM.

##### Optional Value Assignments

Assigning values to choices is optional for each component.  When a component's variation rule does not define values in _any_ of its choices, the value field for that component is not changed when assigning a variation.  This feature is useful for parts that always keep the same value and are only switched between _fitted_ and _unfitted_.

_Note:_ It is important to understand that a component's variation rule must _either_ define **one value for every choice** _or_ **no value for any choice**.  Using a mixture of choices _including_ values and _not including_ values would lead to an inconsistent state of the component value field's content and will therefore raise an error during the plugin's enumeration stage.

##### Default Choice Definitions

Default choices can be used to declare arguments that shall be applied to choices not explicitly defined in the current rule definition, but declared in any other rule definitions (i.e., in rules applied to other components).

As the list of possible aspect choices can be enhanced by other components' rules using the same aspect, not each component (or component variation rule) may be "aware" of the resulting full set of aspect choices built up during the footprint rules enumeration.  Also, defining all possible choices in each component's rule would be tedious and harder to maintain, as all related components' rules would need to be extended when new choices are introduced.  Therefore, default choices are a practical means to define default values and options without explicitly listing all choices they shall apply to.

Default choices are defined in the same way as normal choices.  To indicate a default choice, the character `*` (asterisk) must be used as the choice name.

Beware that default values and default options are applied differently:

 * A **value** listed in a default choice definition applies to _all choices that are not defined or are defined, but do not contain a value assignment_ within the same variation rule.
 * Any **options** listed in a default choice definition only apply to _all choices that are not defined_ within the same variation rule.  That is, if a specific choice is defined in a rule, that definition _always_ overrides all options of the default choice definition.  Options specified in the default choice definition will _not_ be inherited by specific (non-default) choices that are defined in any way inside the same variation rule definition, but only by choices that are exclusively declared (and defined) by _other_ rules (i.e., rules applied to _other components_, but referring to the same variation aspect).

A default choice definition can be placed anywhere in the list of choice definitions, and can also be defined together with other choices (comma-separated notation).  Two recommended ways are to place the default either at the beginning _('default' notation)_ or the end _('else' notation)_ of the choice definitions.  The effect is the same.  It depends on the user's preference how the rule is worded.  For example,

 * `FOO *(10kΩ) BAR,BAZ(47kΩ)` reads like _'Usually a 10kΩ resistor, but for the choices `BAR` or `BAZ`, this becomes a 47kΩ resistor' ('default' notation)._
 * `FOO BAR,BAZ(47kΩ) *(10kΩ)` reads like _'For `BAR` and `BAZ`, this is a 47kΩ resistor; for any other choice, this is a 10kΩ resistor' ('else' notation)._

##### Illustration Example Resolution

For the above illustration example, which was defined as ...

 * `R1` &rarr; `ASPECT_A CHOICE_1(0Ω) CHOICE_2,CHOICE_3(10kΩ)`
 * `R2` &rarr; `ASPECT_A CHOICE_3() *(-!)`

... the following resolution would be computed by KiVar:

|Choice for aspect `ASPECT_A`|Component `R1`             |Component `R2`          |
|----------------------------|---------------------------|------------------------|
|`CHOICE_1`                  |Set value to `0Ω`, fitted  |keep value, **unfitted**|
|`CHOICE_2`                  |Set value to `10kΩ`, fitted|keep value, **unfitted**|
|`CHOICE_3`                  |Set value to `10kΩ`, fitted|keep value, fitted      |

###### Quoting and Escaping

Special characters used for separating parts of a rule definition, such as `,` ` ` `-` `(` `)` (comma, space, dash, parentheses) are **not** considered special (i.e. do not separate parts) when

 * they appear inside a quoted part of the definition, i.e. inside a matching pair of two unescaped `'` (single quotation mark) characters, or when
 * they are escaped, i.e. prepended with a `\` (backslash).

_Note:_ Double quotation mark characters (`"`) are **not** accepted for quoting.

To include any character as-is without being interpreted (e.g. _dash_ to be used as first character of a value, or _single quotation mark_ or _backslash_), that character must be _escaped_, i.e. preceded, with a _backslash_ character.

_Hint:_ In many cases, quoting and escaping in KiVar works just like in a regular POSIX shell interpreter.

_Examples:_

* To assign the fictional value `don't care` (a string containing a single quotation mark and a space), the appropriate value argument in the choice definition would be either `'don\'t care'` or `don\'t\ care`.
* To use `-12V` (a string starting with a dash) as a value, the choice definition arguments `'-12V'` or `\-12V` would be appropriate.  If the dash were not escaped, `-12V` would be interpreted as an (unknown) option.
* To assign an empty component value, use an empty quoted string `''` as choice definition argument.
* To assign a simple single-worded (not separated by a space character) component value, the value does not need to be quoted.  E.g., `10mH` or `'10mH'` are equivalent.

_Note:_ The same rules apply for aspect and choice names.  E.g., the rule `'Aspect Name' 'Choice One'('Value One') Choice\ Two(Value\ Two)` is valid.

_Note:_ When separating parts using the space character (rule definition sections or choice definition arguments), one or more space characters may be used per separation.

#### Constraints

KiVar uses **implicit declarations** for aspects and for choices.  That is, it is not required to maintain a dedicated list of available aspects or choices.  Simply mentioning an aspect or choice inside a rule definition is sufficient to declare them.

_Note:_ Using implicit declarations carries the risk of creating undesired extra aspects or choices in case of spelling errors.  Also, this method may require a little more work in case aspects or choices are to be renamed.  However, the Schematic Editor's _Symbol Fields Table_ is a useful tool for bulk-editing KiVar rules.

#### Real-World Examples

The following examples are taken from a real project and show a few configurable variation aspects, their possible choices along with a short explanation of the implementation.

Each example is illustrated with a schematic snippet including the values of the `KiVar.Rule` field of each related symbol.

##### Example 1: I²C Device Address Selection

This is a very simple example, used for address selection of an I²C device.  Address input A0 switches between device addresses 0x54 _(A0=0)_ and 0x55 _(A0=1)_.

![EEPROM Address Selection](doc/eeprom.png)

The device address is selected by tying the IC input A0 to either +3V3 or GND, depending on the selected choice.  Inputs A1 and A2 are tied to fixed levels.

How to read the rules:

 * Variation aspect is `EEPROM_ADDR` (with choice `0x54` currently applied in the figure).
 * **R1**: For choice `0x55` this part will be fitted (empty definition, hence fitted), else unfitted (per default choice).
 * **R2**: Similarly, for choice `0x54` this part will be fitted, else unfitted.

Alternatively, the rules in this example could explicitly list _those_ choices that make the corresponding parts _unfitted_.  However, with the above notation, the rules can be read more naturally.  That is, choice 0x55 is listed in the upper resistor and leads to high voltage level and choice 0x54 is listed in the lower resistor and leads to low voltage level.

##### Example 2: Boot Source Selection

This is used for the boot source device selection for an NXP i.MX6ULL SoC.

![Boot Source Selection](doc/bootsrc.png)

The variation choices provide selection between the boot sources `EMMC`, `SD` and `NAND`, as well as an extra choice `JP` (which leaves _all_ configuration resistors unfitted, so that the user can configure the board by manually shorting the solder bridges JP1, JP2, JP3).

How to read the rules:

 * Variation aspect is `BOOT_SRC` (with choice `EMMC` currently applied in the figure).
 * **R9**: For choices `NAND` and `JP` this part is unfitted, else (`SD` and `EMMC`) fitted.
 * **R10**: For choices `SD`, `EMMC` and `JP` this part is unfitted, else (`NAND`) fitted.
 * **R11**: For choices `SD`, `NAND` and `JP` this part is unfitted, else (`EMMC`) fitted.

##### Example 3: Undervoltage Trip Points

Typical use-cases for variations are resistor divider networks, such as voltage regulator feedback dividers or — in this case — a voltage divider with two taps for a programmable hysteresis on an undervoltage lock-out (UVLO) circuit.

![UVLO low and high voltage trip points selection](doc/uvlo.png)

The used variation aspect defines all four resistors (only two of them with varying values), allowing to select the lower (cut-off) and higher (recovery) voltage limits for the supply voltage monitor IC.

How to read the rules:

 * Variation aspect is `UVLO_HYST` (with choice `3.15V/3.57V` currently applied in the figure).
 * **R12**: For choice `2.41V/3.40V` the value is `0Ω`, for choice `3.15V/3.57V`, the value is `309kΩ`.
 * **R13**: The value is always set to `1MΩ`.  It is not really required to apply a value, or to use a variation rule at all for this symbol.  However, in case more choices are added in the future, it is very likely that the value of this resistor will change.  Hence the resistor symbol has the rule entry already prepared for easy introduction of new choices.
 * **R14**: For choice `2.41V/3.40V` the value is `309kΩ`, for choice `3.15V/3.57V`, the value is `100kΩ`.
 * **R15**: The value is always set to `750kΩ`.  Same explanation applies as for R13.

##### Example 4: IC Variant Selection

This is used for selection of peripheral parts on a boost-buck-converter IC, which is available as _fixed_ (IRNZ suffix) and _adjustable_ (IRAZ suffix) voltage variants (just like many LDOs are, too).  Depending on the market availability of those IC variants, this variation aspect helps to quickly select between assembly options.

![Switching between fixed and adjustable voltage IC variant](doc/vreg.png)

The fixed voltage IC variant requires a direct feedback of the output voltage to the FB pin, while the adjustable voltage IC variant requires a typical feedback resistor network, including a capacitance of 66pF for stabilization.

How to read the rules:

 * Variation aspect is `ISL91127` (with choice `IRAZ` currently applied in the figure).
 * **C5**, **C6**: For choice `IRNZ` this part is unfitted, else (`IRAZ`) fitted.
 * **R16**: For choice `IRNZ` the value is `0Ω` (fixed version using direct output voltage feedback), for choice `IRAZ` the value is `1MΩ` (adjustable version using a voltage divider for feedback).
 * **R17**: For choice `IRNZ` this part is unfitted (fixed version only has direct feedback, no resistor network), else (`IRAZ`) it is fitted (adjustable version using a voltage divider for feedback).

_Note:_ The rule for **R16** is the _only_ rule explicitly mentioning the choice `IRAZ`, declaring that choice name for all rules that refer to the same variation aspect (`ISL91127`).  For every aspect, you need at least one rule explicitly mentioning a choice for the choice name to be declared and selectable.

_Note:_ In this example, the IC itself keeps its original value (part number without IC variant suffix).  In its current state KiVar can only change part values, no other fields (e.g. ordering information).  If you want to switch between different part types (with different symbols or ordering information) or footprints, you need to use multiple _alternate_ symbol instances with each one defining its own set of relevant fields and only one of them actually fitted (refer to next example).

##### Example 5: IC Type and Address Selection

This is used for selection of an I/O expander IC type (953**5** vs. 953**9**) along with its I²C address.  Different (footprint-compatible!) IC types interpret the input on pin 3 differently ("A2" vs. "/RESET").  See the text callout in the figure for details.

![Device and Address Selection](doc/ioexp.png)

This example really implements two simple aspects in one variation aspect definition: The type of the IC and the device address.  As both aspects depend on each other and can only be defined in a combined way, all possible combinations must be defined.  It is recommended to use the same dedicated sub-aspect separation character (`/` used in this example) in the aspect name as well as the choice names to make it obvious to the user which sub-choice applies to which sub-aspect.

In order to **switch the full set of ordering information or symbol and footprint library references** stored in the symbol fields, this example selects one of two alternate symbol instances, each using a slightly different symbol drawing (note the difference on pin 3).

In general, this variation technique can be used to switch between symbols that refer to either the same footprint (as in this example) or a different footprint shape (e.g. SMT vs. THT, or different SMT package sizes), which can exist side by side or even overlaid in the same spot of the PCB (only the footprints, _not_ the actual components!).

_Hint:_ Should you decide to use multiple overlapping footprint instances (of course, only one of them fitted with the actual component), the following custom DRC rule might become handy:

    (version 1)

    (rule "Allow overlapping courtyards for DNP parts"
        (condition "A.Type == 'Footprint' && B.Type == 'Footprint' && A.Do_not_populate")
        (constraint courtyard_clearance (min -1mm))
    )

_Note:_ If copper pads of multiple _alternate(!)_ footprints do overlap, it is important to assign the same net to each set of overlapping pads, in order to avoid DRC errors.  Some overlapping pads of alternate footprints will be applied the same net anyway (as in this example), but _unconnected_ symbol pins will automatically be applied calculated net names which will naturally conflict with those of alternate symbols if their corresponding copper pads overlap in the PCB.  It is then required to connect the unconnected pins with each other in the schematic (using wires or labels).  In the above example, visually distinguishable labels (P00..P17) were chosen for such connections that are otherwise without function.

How to read the sub-aspects:

This example uses variation aspect `IOEXP_TYPE/ADDR` (read as: sub-aspects `IOEXP_TYPE` and `IOEXP_ADDR`) with choice `9539/0x74` (read as: `9539` selected for `IOEXP_TYPE`, `0x74` selected for `IOEXP_ADDR`) currently applied in the figure.

How to read the rules:

 * Variation aspect is `IOEXP_TYPE/ADDR` (see above).
 * **R18**: This is unfitted by default (i.e. for each choice not defined otherwise in this rule).  For choices `9535/0x24` and `9539/0x74` this part will be fitted (the empty choice definition overrides all options of the default choice, i.e. no "unfit" option set for these specific choices).
 * **R19**: This is unfitted by default (like R18).  For choice `9535/0x20` this part will be fitted (same reason as for R18).
 * **U4**: This rule explicitly lists all choices for which this part is unfitted: `9539/0x74`.  For other choices the part will be fitted.
 * **U5**: This rule explicitly lists all choices for which this part is unfitted: `9535/0x20` and `9539/0x74`.  For other choices the part will be fitted.

##### Example 6: Backlight LED Maximum Constant Current Selection

In this example a combination of resistor networks determines the maximum constant current for an LED backlight (_maximum_ because the used current regulator also has a PWM input, which is later controlled via software).

![Maximum LED backlight current selection](doc/backlight.png)

The resistor network combination allows to select an LED current from 10mA to 150mA in steps of 10mA.  Also, like in example 2, there is an additional choice `JP`, which leaves all four configuration resistors unfitted, so that the user can manually select the current using the solder bridges.

How to read the rules:

 * Variation aspect is `I_LED_MA` (with choice `100` currently applied in the figure).
 * **R21**: This is the _most significant_ path for 80mA current. For the upper half of the current choices, i.e. `80` up to `150`, the resistor is fitted.  For other choices (incl. `JP`) the part will be unfitted.
 * **R22**: This is the path for 40mA current. For choices `40` to `70` and for `120` to `150` the resistor is fitted.  For other choices (incl. `JP`) the part will be unfitted.
 * **R29**: This is the path for 20mA current. For choices `20`, `30`, `60`, `70`, `100`, `110`, `140`, `150` the resistor is fitted.  For other choices (incl. `JP`) the part will be unfitted.
 * **R30**: This is the _least significant_ path for 10mA current. For choices `10`, `30`, `50`, `70`, `90`, `110`, `130`, `150` the resistor is fitted.  For other choices (incl. `JP`) the part will be unfitted.

### Rules Application

After setting up the rules for each relevant symbol (or footprint), variations can finally be switched using the _KiVar_ plugin.

#### Update the PCB

If the rules were set up in the Schematic Editor (eeschema), they need to be updated to the PCB Editor first (menu item _Tools &rarr; Update PCB from Schematic..._).

#### Start the Plugin

To run the plugin, choose the _KiVar_ menu item under _Tools &rarr; External Plugins_ or simply click the KiVar plugin icon in the main toolbar (if configured so).

#### Configuration Identification

Upon start, during the enumeration stage, KiVar automatically detects the current variation configuration, i.e., it tries to find a definite choice for each configured variation, based on the currently assigned values and attributes for each related footprint.

If the values and attributes do not exactly match one definite choice (for a variation aspect), then the corresponding variation choice selector is preset to the entry _'\<unset>'_.  This will probably happen before applying a specific choice for the first time or after editing rules, because not all of the currently assigned footprint attributes may perfectly match one of the defined variation choices.

#### Possible Error Messages

In case the defined variation rules cannot be parsed and enumerated without problems, an error message window with a list of problems will appear.  Each of these problems must then be fixed in order to successfully start the plugin.

_Hint:_ You can click each error message to focus the corresponding footprint on the _pcbnew_ canvas in the background (KiCad 8 and later only).

#### Variation Choices Selection

If all rules can be parsed without problems, the main dialog window appears.

For the above [real-world examples](#real-world-examples), the selection dialog window may look similar to the following:

![Variant Selection Dialog Without Changes](doc/selection-nochange.png)

For each of the listed variation aspects a variation choice can now be selected.

If the values and attributes of the footprint(s) related to a variation aspect shall not be modified, the entry _'\<unset>'_ can be selected for that variation aspect.  In this case, the corresponding variation is skipped during the assignment stage and related footprints remain unmodified.

The change list section below the selection area summarizes all component value and attribute changes to be performed for each related footprint if the current variation configuration is applied.

_Hint:_ You can click each entry in the change list to focus the corresponding footprint on the _pcbnew_ canvas in the background (KiCad 8 and later only).

After selecting a few different variation choices, the dialog window may look like the following:

![Variant Selection Dialog With Changes](doc/selection-change.png)

When clicking the _Update PCB_ button, KiVar sets the values and attributes for all relevant footprints as previewed in the information text box.

#### Visible Changes

The performed changes will immediately be visible in the PCB Editor (e.g. for shown footprint values) and the 3D Viewer window (immediately or after refresh, depending on the preferences setting).

The following images show the 3D board view for the original settings:

![3D Board View Without Changes](doc/pcb-nochange.png)

... and after applying the new variation configuration (according to the dialog window above):

![3D Board View With Changes](doc/pcb-change.png)

#### Updating the Schematic

All changes by the plugin are only performed in the board, as KiVar is a plugin for _pcbnew_ (_eeschema_ does not yet have a plugin interface).  That is, the performed changes must be propagated back from the board to the schematic in order to be visible there (e.g. for changed values and DNP markings).

To propagate the changes back to the schematic, use the PCB Editor menu item _Tools &rarr; Update Schematic from PCB..._ and make sure to select the checkboxes _Values_ and _Attributes_\*.  If you have modified the KiVar rules inside the PCB Editor, i.e. edited the footprint fields\* instead of the symbol fields, then also select the checkbox _Other fields_\*, in order to propagate your KiVar rules to the schematic.

\* _KiCad release 7 does not yet use the concept of footprint fields and can only propagate the footprint value back to the corresponding symbol value.  Also, footprints do not yet have a 'Do not populate' footprint attribute and back-propagation of attributes is not yet supported in release 7.  That is, the 'DNP' state of a schematic symbol can **not** be changed using the 'Update Schematic from PCB...' mechanism.  KiCad releases 8 and later **do** support all of these feartures and therefore provide support for all features currently required by KiVar.  Refer to section '[Supported KiCad Versions](#supported-kicad-versions)' for details._

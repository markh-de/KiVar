# How to Create Documentation Figures

## Schematic Snippet SVGs

Plot all sheets as SVG using the following command (in the `demo/` directory):

```
kicad-cli sch export svg -o plot -e kivar-demo.kicad_sch
```

Then, open each SVG in Inkscape and

 * change the document scale to *0.5 user units per mm* (in Document Properties),
 * select the Documentation Figure Frame,
 * press *Ctrl+Shift+R* (Fit Page to Selection),
 * press *Ctrl+Shift+S* and save as *Plain SVG* to "examples/${number}.svg".

## 3D Images

Resize the 3D viewer window accordingly (max. resolution).

Copy image clipboard, paste to new image in GIMP, export as PNG.

## Vector Screenshots

Used GTK Theme: "Adapta"

Use Vector Screenshot tool to create screenshots of the selection dialog window.

Open each resulting SVG in Inkscape and

 * change the document scale to *1.4 user units per mm* (in Document Properties),
 * select the base rectangle (enter group),
 * add stroke (RGBA: `4d4d4dff` = "70% Gray", *1.5pt* width),
 * press *Ctrl+Shift+R* (Fit Page to Selection),
 * press *Ctrl+Shift+S* and save as *Plain SVG*.

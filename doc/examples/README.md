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


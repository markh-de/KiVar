# How to Create SVG Documentation Figures

In eeschema, plot all sheets as SVG using the following command:

```
kicad-cli sch export svg -o plot -e kivar-demo.kicad_sch
```

Then, open each SVG in Inkscape, click the Documentation Figure Frame,
press "Ctrl+Shift+R", change the document scale to 0.5 user units per mm.

Save as Plain SVG to "examples/${number}.svg".


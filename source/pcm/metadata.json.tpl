{
    "$schema": "https://go.kicad.org/pcm/schemas/v1",
    "name": "KiVar",
    "description": "PCB Assembly Variants for KiCad",
    "description_full": "This plugin provides multi-aspect PCB assembly variant selection.\nIt assigns component values, field content and attributes (such as 'Do not populate') according to variation rules specified in component fields.\n\u2014 Key Concepts \u2014\n\u2022 Designs may contain multiple independent variation aspects (i.e. dimensions or degrees of freedom).\n\u2022 Variation rules are fully contained in the native design files (no external files) and portable (copying parts to another design keeps variation specification intact).\n\u2022 Component data is modified in place, enabling compatibility with any exporter.\n\u2022 No external state information is stored; currently matching variation choices are detected automatically.\n\u2014 Documentation and Demo Project \u2014\nThe variation expression syntax specification and rule examples can be found in the 'Documentation' resource link.\nA demo KiCad project is contained in the source code repository, which can be downloaded as an archive from the 'Source and Demo' resource link.\n\u2014 Support \u2014\nIf you find bugs or want to discuss ideas or questions, please follow the 'Issue Tracker' resource link.",
    "identifier": "de.markh.kivar",
    "type": "plugin",
    "author": {
        "name": "Mark H\u00e4mmerling",
        "contact": {
            "github": "https://github.com/markh-de"
        }
    },
    "license": "MIT",
    "resources": {
        "Documentation": "https://github.com/markh-de/KiVar/blob/v<<VERSION>>/README.md",
        "Source and Demo": "https://github.com/markh-de/KiVar/archive/refs/tags/v<<VERSION>>.zip",
        "Issue Tracker": "https://github.com/markh-de/KiVar/issues",
        "License": "https://raw.githubusercontent.com/markh-de/KiVar/v<<VERSION>>/LICENSE"
    },
    "versions": [
        {
            "version": "<<VERSION>>",
            "status": "testing",
            "kicad_version": "8.0"
        }
    ]
}
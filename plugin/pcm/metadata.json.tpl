{
    "$schema": "https://go.kicad.org/pcm/schemas/v1",
    "name": "KiVar",
    "description": "PCB Assembly Variant Selection for KiCad",
    "description_full": "This plugin provides multi-aspect PCB assembly variant selection.\nIt assigns component values and attributes (such as 'Do not populate') according to variation rules specified in footprint fields.\n\u2014 Key Concepts \u2014\n\u2022 Support for multiple independent variation aspects (i.e., dimensions, degrees of freedom) per design.\n\u2022 Variation rules are fully contained in native design files (no external configuration files) and portable (copying components to another design keeps their variation specification intact).\n\u2022 Seamless integration of the choice selection process, giving the impression of a native KiCad feature.\n\u2022 Component values and attributes are modified in place, enabling compatibility with all exporters that work on the actual component data.\n\u2014 Documentation and Demo Project \u2014\nThe variation rule syntax specification and rule examples can be found in the 'Documentation' resource link.\nA demo KiCad project is contained in the source code repository, which can be downloaded as an archive from the 'Source and Demo' resource link.\n\u2014 Support \u2014\nIf you find bugs or want to discuss ideas or questions, please follow the 'Issue Tracker' resource link.",
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
        "Documentation": "https://github.com/markh-de/KiVar/blob/main/README.md#usage",
        "Source and Demo": "https://github.com/markh-de/KiVar/archive/refs/heads/main.zip",
        "Issue Tracker": "https://github.com/markh-de/KiVar/issues",
        "License": "https://raw.githubusercontent.com/markh-de/KiVar/main/LICENSE"
    },
    "versions": [
        {
            "version": "<<VERSION>>",
            "status": "testing",
            "kicad_version": "7.0"
        }
    ]
}
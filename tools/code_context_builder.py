from typing import Dict


def build_code_context(
    discovery_report: Dict,
    architecture_report: Dict,
    code_unit: Dict
) -> Dict:

    file_path = code_unit[
        "file_path"
    ]

    context = {

        "repository": {

            "name":
                discovery_report.get(
                    "repository_name"
                ),

            "architecture":
                discovery_report.get(
                    "architecture",
                    {}
                ),

            "wcf":
                discovery_report.get(
                    "wcf",
                    {}
                )
        },

        "architecture": {

            "style":
                architecture_report.get(
                    "architecture_style"
                ),

            "summary":
                architecture_report.get(
                    "architecture_summary"
                ),

            "layers":
                architecture_report.get(
                    "layers",
                    []
                ),

            "projects":
                architecture_report.get(
                    "projects",
                    []
                )
        },

        "code_unit":
            code_unit,

        "file_path":
            file_path
    }

    return context 
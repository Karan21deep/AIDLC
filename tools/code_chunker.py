from typing import Dict, List

from tools.code_filter import (
    should_analyze_method
)


def build_code_units(
    parsed_file: Dict
) -> List[Dict]:
    """
    Convert parsed C# AST information into
    meaningful code units.

    A code unit can be:

    1. Class
    2. Method

    Class-level units provide architectural context.

    Method-level units provide detailed business
    logic for important methods.
    """

    units = []

    file_path = parsed_file[
        "file_path"
    ]

    namespace = parsed_file.get(
        "namespace"
    )

    usings = parsed_file.get(
        "usings",
        []
    )

    # =================================================
    # Process each class
    # =================================================

    for class_info in parsed_file.get(
        "classes",
        []
    ):

        class_name = class_info[
            "name"
        ]

        class_source = class_info[
            "source"
        ]

        # =================================================
        # 1. CLASS-LEVEL CODE UNIT
        # =================================================

        units.append({

            "unit_type": "class",

            "file_path":
                file_path,

            "namespace":
                namespace,

            "class_name":
                class_name,

            "method_name":
                None,

            "usings":
                usings,

            "interfaces":
                class_info.get(
                    "interfaces",
                    []
                ),

            "source":
                class_source,

            "start_line":
                class_info.get(
                    "start_line"
                ),

            "end_line":
                class_info.get(
                    "end_line"
                )
        })

        # =================================================
        # 2. METHOD-LEVEL CODE UNITS
        # =================================================

        for method in class_info.get(
            "methods",
            []
        ):

            # ---------------------------------------------
            # Ask the filter whether this method should
            # be analyzed by the LLM.
            # ---------------------------------------------

            if not should_analyze_method(
                method
            ):

                continue

            # ---------------------------------------------
            # Create method-level code unit
            # ---------------------------------------------

            units.append({

                "unit_type": "method",

                "file_path":
                    file_path,

                "namespace":
                    namespace,

                "class_name":
                    class_name,

                "method_name":
                    method.get(
                        "name"
                    ),

                "parameters":
                    method.get(
                        "parameters",
                        []
                    ),

                "source":
                    method.get(
                        "source",
                        ""
                    ),

                "start_line":
                    method.get(
                        "start_line"
                    ),

                "end_line":
                    method.get(
                        "end_line"
                    )
            })

    return units
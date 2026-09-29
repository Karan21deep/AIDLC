from pathlib import Path
from typing import Dict, List

from tree_sitter import Language, Parser
import tree_sitter_c_sharp


C_SHARP_LANGUAGE = Language(
    tree_sitter_c_sharp.language()
)

parser = Parser(C_SHARP_LANGUAGE)


def node_text(
    node,
    source_code: bytes
) -> str:

    return source_code[
        node.start_byte:node.end_byte
    ].decode(
        "utf-8",
        errors="ignore"
    )


def get_namespace(
    root_node,
    source_code: bytes
) -> str | None:

    for node in root_node.children:

        if node.type == "namespace_declaration":

            return node_text(
                node,
                source_code
            )

        if node.type == "file_scoped_namespace_declaration":

            return node_text(
                node,
                source_code
            )

    return None


def extract_usings(
    root_node,
    source_code: bytes
) -> List[str]:

    usings = []

    for node in root_node.children:

        if node.type in {
            "using_directive",
            "global_using_directive"
        }:

            usings.append(
                node_text(
                    node,
                    source_code
                )
            )

    return usings


def find_children(
    node,
    node_types: set
):

    results = []

    for child in node.children:

        if child.type in node_types:

            results.append(child)

    return results


def extract_parameters(
    method_node,
    source_code: bytes
) -> List[str]:

    parameters = []

    for child in method_node.children:

        if child.type == "parameter_list":

            for parameter in child.children:

                if parameter.type == "parameter":

                    parameters.append(
                        node_text(
                            parameter,
                            source_code
                        )
                    )

    return parameters


def extract_methods(
    class_node,
    source_code: bytes
) -> List[Dict]:

    methods = []

    method_types = {
        "method_declaration",
        "constructor_declaration",
        "local_function_statement"
    }

    for child in class_node.children:

        if child.type not in method_types:

            continue

        text = node_text(
            child,
            source_code
        )

        name = None

        for descendant in child.children:

            if descendant.type == "identifier":

                name = node_text(
                    descendant,
                    source_code
                )

                break

        if not name:

            name = "unknown"

        methods.append({

            "name": name,

            "node_type": child.type,

            "source": text,

            "parameters":
                extract_parameters(
                    child,
                    source_code
                ),

            "start_line":
                child.start_point[0] + 1,

            "end_line":
                child.end_point[0] + 1
        })

    return methods


def extract_interfaces(
    class_node,
    source_code: bytes
) -> List[str]:

    interfaces = []

    for child in class_node.children:

        if child.type == "base_list":

            for descendant in child.children:

                if descendant.type in {
                    "identifier",
                    "generic_name"
                }:

                    interfaces.append(
                        node_text(
                            descendant,
                            source_code
                        )
                    )

    return interfaces


def extract_classes(
    root_node,
    source_code: bytes
) -> List[Dict]:

    classes = []

    class_types = {
        "class_declaration",
        "struct_declaration",
        "interface_declaration",
        "record_declaration",
        "record_struct_declaration"
    }

    def walk(node):

        if node.type in class_types:

            name = "unknown"

            for child in node.children:

                if child.type == "identifier":

                    name = node_text(
                        child,
                        source_code
                    )

                    break

            methods = []

            if node.type in {
                "class_declaration",
                "record_declaration"
            }:

                methods = extract_methods(
                    node,
                    source_code
                )

            classes.append({

                "name": name,

                "type": node.type,

                "source": node_text(
                    node,
                    source_code
                ),

                "interfaces":
                    extract_interfaces(
                        node,
                        source_code
                    ),

                "methods": methods,

                "start_line":
                    node.start_point[0] + 1,

                "end_line":
                    node.end_point[0] + 1
            })

        for child in node.children:

            walk(child)

    walk(root_node)

    return classes


def parse_csharp_file(
    file_path: str
) -> Dict:

    path = Path(file_path)

    source_code = path.read_bytes()

    tree = parser.parse(
        source_code
    )

    root_node = tree.root_node

    return {

        "file_path":
            str(path),

        "namespace":
            get_namespace(
                root_node,
                source_code
            ),

        "usings":
            extract_usings(
                root_node,
                source_code
            ),

        "classes":
            extract_classes(
                root_node,
                source_code
            )
    }

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List


def read_file(
    file_path: Path
) -> str:

    try:

        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


def analyze_project_file(
    repo_path: str,
    project_path: str
) -> Dict:

    root = Path(repo_path)

    path = root / project_path

    content = read_file(path)

    result = {
        "project": project_path,
        "target_framework": None,
        "project_references": [],
        "package_references": [],
        "assembly_references": [],
    }

    if not content:
        return result

    try:

        xml_root = ET.fromstring(
            content
        )

    except ET.ParseError:

        return result

    # ------------------------------------------------
    # Target framework
    # ------------------------------------------------

    for element in xml_root.iter():

        tag = element.tag.split("}")[-1]

        if tag in {
            "TargetFramework",
            "TargetFrameworkVersion",
            "TargetFrameworks"
        }:

            result["target_framework"] = (
                element.text
            )

    # ------------------------------------------------
    # Project references
    # ------------------------------------------------

    for element in xml_root.iter():

        tag = element.tag.split("}")[-1]

        if tag == "ProjectReference":

            include = element.attrib.get(
                "Include"
            )

            if include:

                result[
                    "project_references"
                ].append(include)

    # ------------------------------------------------
    # Package references
    # ------------------------------------------------

    for element in xml_root.iter():

        tag = element.tag.split("}")[-1]

        if tag == "PackageReference":

            include = element.attrib.get(
                "Include"
            )

            version = element.attrib.get(
                "Version"
            )

            if include:

                result[
                    "package_references"
                ].append({
                    "name": include,
                    "version": version
                })

    return result


def collect_project_structure(
    repo_path: str,
    project_path: str
) -> Dict:

    root = Path(repo_path)

    project_file = root / project_path

    project_directory = project_file.parent

    files = []

    directories = set()

    if project_directory.exists():

        for path in project_directory.rglob("*"):

            if not path.is_file():
                continue

            if any(
                ignored in path.parts
                for ignored in {
                    ".git",
                    ".vs",
                    "bin",
                    "obj",
                    "packages"
                }
            ):
                continue

            relative = str(
                path.relative_to(root)
            )

            files.append(relative)

            relative_parent = path.parent.relative_to(
                project_directory
            )

            if str(relative_parent) != ".":

                directories.add(
                    str(relative_parent)
                )

    return {
        "project": project_path,
        "files": files,
        "directories": sorted(
            directories
        )
    }


def scan_architecture(
    repo_path: str,
    project_files: List[str]
) -> Dict:

    project_information = []

    for project in project_files:

        project_data = analyze_project_file(
            repo_path,
            project
        )

        structure = collect_project_structure(
            repo_path,
            project
        )

        project_information.append({
            **project_data,
            "structure": structure
        })

    return {
        "projects": project_information
    }
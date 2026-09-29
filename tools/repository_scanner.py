from pathlib import Path
from typing import Dict, List


IGNORED_DIRECTORIES = {
    ".git",
    ".vs",
    "bin",
    "obj",
    "node_modules",
    ".idea",
    "__pycache__",
    "packages",
}

SOURCE_EXTENSIONS = {
    ".cs",
    ".cshtml",
    ".razor",
}

CONFIG_EXTENSIONS = {
    ".config",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
}


def scan_repository(repo_path: str) -> Dict:

    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repo_path}"
        )

    files: List[str] = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        # Ignore build / git directories
        if any(
            ignored in path.parts
            for ignored in IGNORED_DIRECTORIES
        ):
            continue

        relative_path = str(path.relative_to(root))

        files.append(relative_path)

    solution_files = [
        f for f in files
        if f.lower().endswith(".sln")
    ]

    project_files = [
        f for f in files
        if f.lower().endswith(".csproj")
    ]

    source_files = [
        f for f in files
        if Path(f).suffix.lower() in SOURCE_EXTENSIONS
    ]

    config_files = [
        f for f in files
        if Path(f).suffix.lower() in CONFIG_EXTENSIONS
    ]

    wcf_files = [
        f for f in files
        if f.lower().endswith(".svc")
    ]

    interface_files = [
        f for f in source_files
        if Path(f).name.startswith("I")
    ]

    test_files = [
        f for f in project_files
        if "test" in f.lower()
    ]

    return {
        "repository_name": root.name,

        "total_files": len(files),

        "source_file_count": len(source_files),

        "files": files,

        "solution_files": solution_files,

        "project_files": project_files,

        "source_files": source_files,

        "configuration_files": config_files,

        "wcf_service_files": wcf_files,

        "interface_files": interface_files,

        "test_projects": test_files,
    }

def read_text_file(root: Path, relative_path: str) -> str:

    file_path = root / relative_path

    try:
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception:
        return ""

def collect_project_content(
    repo_path: str,
    project_files: List[str]
) -> Dict[str, str]:

    root = Path(repo_path)

    result = {}

    for project in project_files:

        content = read_text_file(
            root,
            project
        )

        result[project] = content

    return result


def detect_wcf(
    root: Path,
    files: List[str]
) -> Dict:

    wcf_files = []

    contracts = []

    bindings = []

    endpoints = []

    configuration_files = []

    for relative_file in files:

        file_path = root / relative_file

        try:

            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        except Exception:
            continue

        lower_content = content.lower()

        # .svc files
        if file_path.suffix.lower() == ".svc":
            wcf_files.append(relative_file)

        # WCF contracts
        if "servicecontract" in lower_content:
            contracts.append(relative_file)

        if "operationcontract" in lower_content:
            contracts.append(relative_file)

        # WCF configuration
        if "basichttpbinding" in lower_content:
            bindings.append("basicHttpBinding")

        if "wshttpbinding" in lower_content:
            bindings.append("wsHttpBinding")

        if "nettcpbinding" in lower_content:
            bindings.append("netTcpBinding")

        if "<endpoint" in lower_content:
            endpoints.append(relative_file)

        if (
            file_path.name.lower()
            in {"web.config", "app.config"}
        ):
            if (
                "system.servicemodel"
                in lower_content
            ):
                configuration_files.append(
                    relative_file
                )

    return {
        "detected": bool(
            wcf_files
            or contracts
            or bindings
            or endpoints
        ),
        "service_files": list(set(wcf_files)),
        "contracts": list(set(contracts)),
        "bindings": list(set(bindings)),
        "endpoints": list(set(endpoints)),
        "configuration_files": list(
            set(configuration_files)
        ),
    }
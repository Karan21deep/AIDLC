IMPORTANT_METHOD_NAMES = {
    "get",
    "create",
    "update",
    "delete",
    "save",
    "execute",
    "process",
    "validate",
    "handle",
    "insert",
    "remove",
    "search",
    "find",
    "authenticate",
    "authorize",
}



def classify_file(
    file_path: str
) -> str:

    path = file_path.lower()

    if (
        "unittest" in path
        or ".test" in path
        or "tests" in path
        or "test" in path
    ):
        return "unit_test"

    if (
        ".svc" in path
        or "service" in path
    ):
        return "service"

    if (
        "repository" in path
        or "dataaccess" in path
        or "data_access" in path
    ):
        return "data_access"

    if (
        "controller" in path
    ):
        return "controller"

    if (
        "dto" in path
        or "model" in path
    ):
        return "model"

    return "application"


def should_analyze_method(method: dict) -> bool:
    """
    Determine whether a method should be analyzed
    by the LLM.
    """

    name = method.get(
        "name",
        ""
    ).lower()

    source = method.get(
        "source",
        ""
    )

    # ---------------------------------------------
    # Skip constructors
    # ---------------------------------------------

    if name.startswith(".ctor"):
        return False

    # ---------------------------------------------
    # IMPORTANT:
    # Analyze important business methods even if
    # they are very short.
    # ---------------------------------------------

    for keyword in IMPORTANT_METHOD_NAMES:

        if keyword in name:

            return True

    # ---------------------------------------------
    # Skip extremely small methods
    # ---------------------------------------------

    if len(source.strip()) < 100:

        return False

    # ---------------------------------------------
    # Analyze all remaining meaningful methods
    # ---------------------------------------------

    return True
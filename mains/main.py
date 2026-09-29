import json
import traceback
import os
import hashlib

from pathlib import Path

from dotenv import load_dotenv

from agents.code_understanding_agent import (
    CodeUnderstandingAgent
)


# =========================================================
# Cache Configuration
# =========================================================

CACHE_FILE = (
    "output/code_analysis_cache.json"
)


# =========================================================
# Load JSON file
# =========================================================

def load_json(path: str) -> dict:

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"Required file not found: {path}\n"
            f"Please run the Repository Discovery Agent "
            f"and Architecture Analysis Agent first."
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# Find C# files
# =========================================================

def find_csharp_files(
    repo_path: str
) -> list[Path]:

    root = Path(repo_path)

    if not root.exists():

        raise FileNotFoundError(
            f"Repository path does not exist: {repo_path}"
        )

    if not root.is_dir():

        raise NotADirectoryError(
            f"Repository path is not a directory: {repo_path}"
        )

    ignored_directories = {
        ".git",
        ".vs",
        "bin",
        "obj",
        "packages",
        "node_modules",
        ".idea",
        "__pycache__"
    }

    cs_files = []

    for file in root.rglob("*.cs"):

        # Ignore generated/build directories
        if any(
            ignored in file.parts
            for ignored in ignored_directories
        ):
            continue

        cs_files.append(file)

    return sorted(cs_files)


# =========================================================
# Calculate file hash
# =========================================================

def calculate_file_hash(
    file_path: Path
) -> str:

    """
    Calculate SHA-256 hash of the C# file.

    If the file content changes, the hash changes.
    This allows us to detect whether the file needs
    to be analyzed again.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):

            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# Load Code Analysis Cache
# =========================================================

def load_cache() -> dict:

    cache_path = Path(
        CACHE_FILE
    )

    if not cache_path.exists():

        print(
            "\nNo existing code analysis cache found."
        )

        return {}

    try:

        with open(
            cache_path,
            "r",
            encoding="utf-8"
        ) as file:

            cache = json.load(file)

        print(
            f"\nLoaded code analysis cache "
            f"with {len(cache)} entries."
        )

        return cache

    except Exception as error:

        print(
            "\nWARNING: Could not load cache."
        )

        print(
            f"Cache error: {error}"
        )

        print(
            "A new cache will be created."
        )

        return {}


# =========================================================
# Save Code Analysis Cache
# =========================================================

def save_cache(
    cache: dict
):

    cache_path = Path(
        CACHE_FILE
    )

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Write to temporary file first
    # so that cache is not corrupted
    # if the process stops during writing.

    temp_path = cache_path.with_suffix(
        ".tmp"
    )

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cache,
            file,
            indent=2,
            ensure_ascii=False
        )

    temp_path.replace(
        cache_path
    )


# =========================================================
# Check whether cached result is valid
# =========================================================

def get_cached_result(
    file_path: Path,
    cache: dict
):

    """
    Return cached result if:

    1. File exists in cache
    2. Previous status was SUCCESS
    3. File hash has not changed

    Otherwise return None.
    """

    file_key = str(
        file_path.resolve()
    )

    cached_entry = cache.get(
        file_key
    )

    if not cached_entry:

        return None

    # Only reuse successful results.
    if cached_entry.get(
        "status"
    ) != "success":

        return None

    current_hash = calculate_file_hash(
        file_path
    )

    cached_hash = cached_entry.get(
        "file_hash"
    )

    if current_hash != cached_hash:

        print(
            "File has changed since "
            "previous analysis."
        )

        return None

    return cached_entry.get(
        "result"
    )


# =========================================================
# Store successful result in cache
# =========================================================

def store_success(
    file_path: Path,
    result: dict,
    cache: dict
):

    file_key = str(
        file_path.resolve()
    )

    file_hash = calculate_file_hash(
        file_path
    )

    cache[file_key] = {

        "file_hash":
            file_hash,

        "status":
            "success",

        "result":
            result
    }

    # Save immediately.
    #
    # This is important because if the program
    # crashes after processing 30 files, those
    # 30 successful files will already be cached.

    save_cache(
        cache
    )


# =========================================================
# Store failed result
# =========================================================

def store_failure(
    file_path: Path,
    error: Exception,
    cache: dict
):

    file_key = str(
        file_path.resolve()
    )

    file_hash = calculate_file_hash(
        file_path
    )

    cache[file_key] = {

        "file_hash":
            file_hash,

        "status":
            "failed",

        "error":
            str(error)
    }

    # Save failure information for visibility,
    # but get_cached_result() will never reuse
    # a failed result.

    save_cache(
        cache
    )


# =========================================================
# Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Load environment variables
    # -----------------------------------------------------

    load_dotenv()

    print("=" * 70)

    print(
        "       CODE UNDERSTANDING AGENT"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # Ask repository path
    # -----------------------------------------------------

    repo_path = input(
        "\nEnter repository path: "
    ).strip()

    if not repo_path:

        print(
            "ERROR: Repository path cannot be empty."
        )

        return

    # -----------------------------------------------------
    # Existing reports
    #
    # We DO NOT execute:
    #
    # 1. Repository Discovery Agent
    # 2. Architecture Analysis Agent
    #
    # We only load their existing JSON outputs.
    # -----------------------------------------------------

    discovery_report_path = (
        "output/discovery_report.json"
    )

    architecture_report_path = (
        "output/architecture_report.json"
    )

    print(
        "\nLoading existing discovery report..."
    )

    discovery_report = load_json(
        discovery_report_path
    )

    print(
        "Discovery report loaded."
    )

    print(
        "\nLoading existing architecture report..."
    )

    architecture_report = load_json(
        architecture_report_path
    )

    print(
        "Architecture report loaded."
    )

    # -----------------------------------------------------
    # Create Code Understanding Agent
    # -----------------------------------------------------

    print(
        "\nInitializing Code Understanding Agent..."
    )

    agent = CodeUnderstandingAgent()

    # -----------------------------------------------------
    # Find C# files
    # -----------------------------------------------------

    print(
        "\nScanning repository for C# files..."
    )

    cs_files = find_csharp_files(
        repo_path
    )

    print(
        f"Found {len(cs_files)} C# files."
    )

    if not cs_files:

        print(
            "\nNo C# files found in the repository."
        )

        return

    # -----------------------------------------------------
    # Load cache
    # -----------------------------------------------------

    cache = load_cache()

    # -----------------------------------------------------
    # Results
    # -----------------------------------------------------

    results = []

    total_files = len(
        cs_files
    )

    processed = 0

    cached = 0

    failed = 0

    # -----------------------------------------------------
    # Analyze each C# file
    # -----------------------------------------------------

    for index, file in enumerate(
        cs_files,
        start=1
    ):

        print(
            "\n" + "-" * 70
        )

        print(
            f"[{index}/{total_files}] "
            f"Analyzing:"
        )

        print(
            f"{file}"
        )

        # -------------------------------------------------
        # Check cache
        # -------------------------------------------------

        try:

            cached_result = get_cached_result(
                file,
                cache
            )

        except Exception as cache_error:

            print(
                "\nWARNING: Could not validate cache."
            )

            print(
                f"Cache validation error: "
                f"{cache_error}"
            )

            cached_result = None

        # -------------------------------------------------
        # CACHE HIT
        # -------------------------------------------------

        if cached_result is not None:

            print(
                "Status: CACHE HIT"
            )

            print(
                "Skipping OpenAI processing."
            )

            results.append(
                cached_result
            )

            cached += 1

            continue

        # -------------------------------------------------
        # CACHE MISS
        # -------------------------------------------------

        print(
            "Status: CACHE MISS"
        )

        print(
            "Processing file with OpenAI..."
        )

        # -------------------------------------------------
        # Call Code Understanding Agent
        # -------------------------------------------------

        try:

            result = agent.analyze_file(

                file_path=str(file),

                discovery_report=
                    discovery_report,

                architecture_report=
                    architecture_report
            )

            result_dict = (
                result.model_dump()
            )

            # ---------------------------------------------
            # Store successful result immediately
            # ---------------------------------------------

            store_success(

                file_path=file,

                result=result_dict,

                cache=cache
            )

            results.append(
                result_dict
            )

            processed += 1

            print(
                "Status: SUCCESS"
            )

            print(
                "Result saved to cache."
            )

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        except Exception as error:

            print(
                "Status: FAILED"
            )

            print(
                f"Error: {error}"
            )

            print(
                "\nFull traceback:"
            )

            traceback.print_exc()

            # ---------------------------------------------
            # Save failure information
            # ---------------------------------------------

            try:

                store_failure(

                    file_path=file,

                    error=error,

                    cache=cache
                )

            except Exception as cache_error:

                print(
                    "\nWARNING: Could not save "
                    "failure to cache."
                )

                print(
                    f"Cache error: "
                    f"{cache_error}"
                )

            failed += 1

            # ---------------------------------------------
            # Add failure to current output
            # ---------------------------------------------

            results.append({

                "file_path":
                    str(file),

                "error":
                    str(error)
            })

    # -----------------------------------------------------
    # Save final results
    # -----------------------------------------------------

    output_directory = Path(
        "output"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_directory
        / "code_analysis.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    successful = sum(

        1

        for result in results

        if "error" not in result
    )

    current_failed = sum(

        1

        for result in results

        if "error" in result
    )

    # -----------------------------------------------------
    # Final output
    # -----------------------------------------------------

    print("\n")

    print(
        "=" * 70
    )

    print(
        "       CODE UNDERSTANDING COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nTotal C# files : {total_files}"
    )

    print(
        f"Processed      : {processed}"
    )

    print(
        f"Cached         : {cached}"
    )

    print(
        f"Successful     : {successful}"
    )

    print(
        f"Failed         : {current_failed}"
    )

    print(
        f"\nOutput file:"
    )

    print(
        f"{output_path}"
    )

    print(
        f"\nCache file:"
    )

    print(
        f"{CACHE_FILE}"
    )

    print(
        "\nThe following existing reports were used:"
    )

    print(
        f"1. {discovery_report_path}"
    )

    print(
        f"2. {architecture_report_path}"
    )

    print(
        "\nNo Discovery or Architecture Agent "
        "was executed."
    )


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":

    main()
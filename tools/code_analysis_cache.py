import hashlib
import json
from pathlib import Path


class CodeAnalysisCache:

    def __init__(self, cache_file="output/code_analysis_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self._load()

    def _load(self):
        if not self.cache_file.exists():
            return {}

        try:
            with open(
                self.cache_file,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except Exception:
            return {}

    def save(self):
        self.cache_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_file = self.cache_file.with_suffix(".tmp")

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.cache,
                f,
                indent=2,
                ensure_ascii=False
            )

        temp_file.replace(self.cache_file)

    @staticmethod
    def calculate_hash(file_path):
        sha256 = hashlib.sha256()

        with open(
            file_path,
            "rb"
        ) as f:

            for chunk in iter(
                lambda: f.read(1024 * 1024),
                b""
            ):
                sha256.update(chunk)

        return sha256.hexdigest()

    def get(self, file_path):

        file_key = str(
            Path(file_path).resolve()
        )

        return self.cache.get(file_key)

    def is_valid(self, file_path):

        file_key = str(
            Path(file_path).resolve()
        )

        entry = self.cache.get(file_key)

        if not entry:
            return False

        if entry.get("status") != "success":
            return False

        current_hash = self.calculate_hash(
            file_path
        )

        return (
            entry.get("file_hash")
            == current_hash
        )

    def get_result(self, file_path):

        file_key = str(
            Path(file_path).resolve()
        )

        entry = self.cache.get(file_key)

        if not entry:
            return None

        return entry.get("result")

    def store_success(
        self,
        file_path,
        result
    ):

        file_key = str(
            Path(file_path).resolve()
        )

        file_hash = self.calculate_hash(
            file_path
        )

        self.cache[file_key] = {
            "file_hash": file_hash,
            "status": "success",
            "result": result
        }

        self.save()

    def store_failure(
        self,
        file_path,
        error
    ):

        file_key = str(
            Path(file_path).resolve()
        )

        file_hash = self.calculate_hash(
            file_path
        )

        self.cache[file_key] = {
            "file_hash": file_hash,
            "status": "failed",
            "error": str(error)
        }

        self.save()
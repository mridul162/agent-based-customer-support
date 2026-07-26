import json
from pathlib import Path


class ManifestManager:

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(
            manifest_path
        )

    def load(self) -> dict:

        if not self.manifest_path.exists():
            return {}

        with open(
            self.manifest_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def save(
        self,
        manifest: dict
    ):

        self.manifest_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.manifest_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                manifest,
                f,
                indent=2,
                ensure_ascii=False
            )


if __name__ == "__main__":
    manager = ManifestManager(
        "artifacts/embeddings/manifest.json"
    )

    manifest = manager.load()
    print(manifest)
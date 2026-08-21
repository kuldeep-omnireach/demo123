import json
from pathlib import Path


# =========================================================
# Project Paths
# =========================================================

# This script is located at:
# /ros-coveo-config-poc/src/scripts/pull_snapshot.py
#
# Go up:
# scripts -> src -> ros-coveo-config-poc
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SNAPSHOT_FILE = (
    PROJECT_ROOT
    / "dump"
    / "Snapshot-resmednonproduction1fl4b3vdz-vf2zo4y5j6d7j5stvtl3jt2i4m.json"
)

SRC_DIR = PROJECT_ROOT / "src"


# =========================================================
# Main
# =========================================================

def main():
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Reading snapshot: {SNAPSHOT_FILE}")
    print(f"Output directory: {SRC_DIR}")
    print()

    if not SNAPSHOT_FILE.exists():
        raise FileNotFoundError(
            f"Snapshot file not found:\n{SNAPSHOT_FILE}"
        )

    # Read full snapshot JSON
    with SNAPSHOT_FILE.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    # Coveo snapshot resources
    resources = snapshot.get("resources")

    if not isinstance(resources, dict):
        raise ValueError(
            "Invalid snapshot format. "
            "Expected a 'resources' object in the JSON."
        )

    # Make sure src exists
    SRC_DIR.mkdir(parents=True, exist_ok=True)

    written_count = 0

    for section_name, section_data in resources.items():

        # Example:
        # src/CATALOG
        # src/FIELD
        # src/SOURCE
        section_dir = SRC_DIR / section_name

        # Automatically create folder if missing
        section_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Example:
        # src/CATALOG/CATALOG.json
        output_file = section_dir / f"{section_name}.json"

        # Keep only this resource section
        output_data = {
            section_name: section_data
        }

        # Write JSON
        with output_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=2,
                ensure_ascii=False
            )

            file.write("\n")

        print(f"[OK] {section_name}")
        print(f"     {output_file}")

        written_count += 1

    print()
    print("=========================================")
    print(f"Completed. {written_count} sections written.")
    print("=========================================")


if __name__ == "__main__":
    main()
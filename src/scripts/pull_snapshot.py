import json
from pathlib import Path


# =========================================================
# Project Paths
# =========================================================

# Script location:
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

MANIFEST_FILE = SRC_DIR / "snapshot-manifest.json"


# =========================================================
# Helpers
# =========================================================

def load_snapshot():
    """
    Load and validate the Coveo snapshot.
    """

    if not SNAPSHOT_FILE.exists():
        raise FileNotFoundError(
            f"Snapshot file not found:\n{SNAPSHOT_FILE}"
        )

    with SNAPSHOT_FILE.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    if not isinstance(snapshot, dict):
        raise ValueError(
            "Invalid snapshot. Root JSON must be an object."
        )

    metadata = snapshot.get("metadata")

    if not isinstance(metadata, dict):
        raise ValueError(
            "Invalid snapshot. Expected a 'metadata' object."
        )

    resources = snapshot.get("resources")

    if not isinstance(resources, dict):
        raise ValueError(
            "Invalid snapshot. Expected a 'resources' object."
        )

    return snapshot


def write_manifest(snapshot):
    """
    Preserve information required to rebuild the snapshot exactly.

    The manifest stores:
    - snapshot metadata
    - original resource section order
    - managed section names
    """

    resources = snapshot["resources"]

    manifest = {
        "metadata": snapshot["metadata"],
        "resourceOrder": list(resources.keys()),
        "managedSections": list(resources.keys())
    }

    with MANIFEST_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")

    print("[OK] Manifest")
    print(f"     {MANIFEST_FILE}")


def write_section(section_name, section_data):
    """
    Write one resource section.

    Example:

    src/CATALOG/CATALOG.json

    {
      "CATALOG": [
        ...
      ]
    }
    """

    section_dir = SRC_DIR / section_name

    section_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        section_dir
        / f"{section_name}.json"
    )

    output_data = {
        section_name: section_data
    }

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

    item_count = (
        len(section_data)
        if isinstance(section_data, list)
        else 1
    )

    print(
        f"[OK] {section_name:<30} "
        f"{item_count} item(s)"
    )


def find_stale_sections(current_sections):
    """
    Detect section folders that were previously managed
    but are no longer present in the current snapshot.

    This version reports them but DOES NOT delete anything.
    """

    if not MANIFEST_FILE.exists():
        return []

    try:
        with MANIFEST_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            old_manifest = json.load(file)

    except Exception:
        return []

    old_sections = old_manifest.get(
        "managedSections",
        []
    )

    if not isinstance(old_sections, list):
        return []

    current_set = set(current_sections)

    return [
        section
        for section in old_sections
        if section not in current_set
    ]


# =========================================================
# Main
# =========================================================

def main():

    print("=========================================")
    print("Coveo Snapshot Pull")
    print("=========================================")

    print(f"Project root    : {PROJECT_ROOT}")
    print(f"Snapshot        : {SNAPSHOT_FILE}")
    print(f"Output directory: {SRC_DIR}")
    print()

    # -----------------------------------------------------
    # Read snapshot
    # -----------------------------------------------------

    snapshot = load_snapshot()

    metadata = snapshot["metadata"]
    resources = snapshot["resources"]

    # -----------------------------------------------------
    # Ensure src exists
    # -----------------------------------------------------

    SRC_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Detect stale sections BEFORE replacing manifest
    # -----------------------------------------------------

    stale_sections = find_stale_sections(
        resources.keys()
    )

    # -----------------------------------------------------
    # Write individual resource sections
    # -----------------------------------------------------

    written_count = 0
    total_resources = 0

    for section_name, section_data in resources.items():

        if not isinstance(section_name, str):
            raise ValueError(
                "Resource section name must be a string."
            )

        if not isinstance(
            section_data,
            (list, dict)
        ):
            raise ValueError(
                f"Invalid resource section "
                f"'{section_name}'. "
                f"Expected list or object."
            )

        write_section(
            section_name,
            section_data
        )

        written_count += 1

        if isinstance(section_data, list):
            total_resources += len(section_data)
        else:
            total_resources += 1

    # -----------------------------------------------------
    # Write manifest LAST
    #
    # This ensures the manifest is only updated after all
    # sections have been written successfully.
    # -----------------------------------------------------

    write_manifest(snapshot)

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print()
    print("=========================================")
    print("Pull completed successfully.")
    print(f"Schema version : {metadata.get('schemaVersion')}")
    print(f"Sections       : {written_count}")
    print(f"Total resources: {total_resources}")
    print("=========================================")

    # -----------------------------------------------------
    # Stale resource warning
    # -----------------------------------------------------

    if stale_sections:

        print()
        print("[WARN] Stale managed section folders detected:")

        for section in stale_sections:
            print(
                f"       src/{section}/"
            )

        print()
        print(
            "These sections existed in the previous snapshot "
            "but are not present in the current snapshot."
        )

        print(
            "They were NOT deleted automatically."
        )


if __name__ == "__main__":
    main()
import json
from pathlib import Path


# =========================================================
# Project Paths
# =========================================================

# Script location:
# /ros-coveo-config-poc/src/scripts/merge_snapshot.py
#
# Go up:
# scripts -> src -> ros-coveo-config-poc
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SRC_DIR = PROJECT_ROOT / "src"

MANIFEST_FILE = SRC_DIR / "snapshot-manifest.json"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "dump"
    / "Merged-Snapshot-resmednonproduction1fl4b3vdz-vf2zo4y5j6d7j5stvtl3jt2i4m.json"
)


# =========================================================
# Manifest
# =========================================================

def load_manifest():
    """
    Load snapshot metadata and original resource order
    created by pull_snapshot.py.
    """

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            "Snapshot manifest not found:\n"
            f"{MANIFEST_FILE}\n\n"
            "Run pull_snapshot.py first."
        )

    with MANIFEST_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError(
            "Invalid manifest. Root must be a JSON object."
        )

    metadata = manifest.get("metadata")

    if not isinstance(metadata, dict):
        raise ValueError(
            "Invalid manifest. Expected 'metadata' object."
        )

    resource_order = manifest.get("resourceOrder")

    if not isinstance(resource_order, list):
        raise ValueError(
            "Invalid manifest. Expected 'resourceOrder' array."
        )

    if not resource_order:
        raise ValueError(
            "Manifest contains no resource sections."
        )

    managed_sections = manifest.get(
        "managedSections",
        resource_order
    )

    if not isinstance(managed_sections, list):
        raise ValueError(
            "Invalid manifest. Expected 'managedSections' array."
        )

    return (
        metadata,
        resource_order,
        managed_sections
    )


# =========================================================
# Read Resource Section
# =========================================================

def read_section(section_name):
    """
    Read:

    src/CATALOG/CATALOG.json

    Expected format:

    {
      "CATALOG": [
        ...
      ]
    }

    Returns only the section content.
    """

    section_file = (
        SRC_DIR
        / section_name
        / f"{section_name}.json"
    )

    if not section_file.exists():
        raise FileNotFoundError(
            f"Required resource section is missing:\n"
            f"{section_file}"
        )

    with section_file.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid section file:\n"
            f"{section_file}\n"
            f"Expected a JSON object."
        )

    if section_name not in data:
        raise ValueError(
            f"Invalid section file:\n"
            f"{section_file}\n"
            f"Expected key '{section_name}'."
        )

    # Make sure the file contains only its own section
    unexpected_keys = [
        key
        for key in data.keys()
        if key != section_name
    ]

    if unexpected_keys:
        raise ValueError(
            f"Section file contains unexpected keys:\n"
            f"{section_file}\n"
            f"{unexpected_keys}"
        )

    section_data = data[section_name]

    if not isinstance(
        section_data,
        (list, dict)
    ):
        raise ValueError(
            f"Invalid data type for section "
            f"'{section_name}'. "
            f"Expected list or object."
        )

    return section_data


# =========================================================
# Detect Extra Sections
# =========================================================

def find_extra_sections(managed_sections):
    """
    Find folders under src that look like resource sections
    but are not registered in the manifest.

    Example:

    src/OLD_SECTION/OLD_SECTION.json

    These are warned about but not merged.
    """

    managed_set = set(managed_sections)

    extra_sections = []

    for directory in SRC_DIR.iterdir():

        if not directory.is_dir():
            continue

        section_name = directory.name

        matching_file = (
            directory
            / f"{section_name}.json"
        )

        if (
            matching_file.exists()
            and section_name not in managed_set
        ):
            extra_sections.append(
                section_name
            )

    return sorted(extra_sections)


# =========================================================
# Main
# =========================================================

def main():

    print("=========================================")
    print("Coveo Snapshot Merge")
    print("=========================================")

    print(f"Project root    : {PROJECT_ROOT}")
    print(f"Source directory: {SRC_DIR}")
    print(f"Manifest        : {MANIFEST_FILE}")
    print(f"Output snapshot : {OUTPUT_FILE}")
    print()

    if not SRC_DIR.exists():
        raise FileNotFoundError(
            f"Source directory not found:\n"
            f"{SRC_DIR}"
        )

    # -----------------------------------------------------
    # Load manifest
    # -----------------------------------------------------

    (
        metadata,
        resource_order,
        managed_sections
    ) = load_manifest()

    print(
        f"Manifest contains "
        f"{len(resource_order)} sections."
    )

    print()

    # -----------------------------------------------------
    # Detect unmanaged / stale extra sections
    # -----------------------------------------------------

    extra_sections = find_extra_sections(
        managed_sections
    )

    if extra_sections:

        print(
            "[WARN] Extra resource folders detected "
            "that are not present in the manifest:"
        )

        for section in extra_sections:
            print(
                f"       src/{section}/"
            )

        print()
        print(
            "These sections will NOT be included "
            "in the merged snapshot."
        )

        print()

    # -----------------------------------------------------
    # Read resources using ORIGINAL order from manifest
    # -----------------------------------------------------

    resources = {}

    total_resources = 0

    for section_name in resource_order:

        if not isinstance(section_name, str):
            raise ValueError(
                "Invalid manifest. "
                "Resource section names must be strings."
            )

        section_data = read_section(
            section_name
        )

        resources[section_name] = section_data

        item_count = (
            len(section_data)
            if isinstance(section_data, list)
            else 1
        )

        total_resources += item_count

        print(
            f"[OK] {section_name:<30} "
            f"{item_count} item(s)"
        )

    # -----------------------------------------------------
    # Final validation
    # -----------------------------------------------------

    expected_sections = set(
        resource_order
    )

    actual_sections = set(
        resources.keys()
    )

    missing_sections = (
        expected_sections
        - actual_sections
    )

    if missing_sections:
        raise ValueError(
            "Merge failed. Missing sections:\n"
            + "\n".join(
                sorted(missing_sections)
            )
        )

    # -----------------------------------------------------
    # Build snapshot
    # -----------------------------------------------------

    merged_snapshot = {
        "metadata": metadata,
        "resources": resources
    }

    # -----------------------------------------------------
    # Ensure dump directory exists
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Write merged snapshot
    # -----------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            merged_snapshot,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")

    # -----------------------------------------------------
    # Verify output can be read back
    # -----------------------------------------------------

    with OUTPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        verification = json.load(file)

    if verification != merged_snapshot:
        raise ValueError(
            "Output verification failed. "
            "Written snapshot does not match "
            "the generated snapshot."
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print()
    print("=========================================")
    print("Merge completed successfully.")
    print(
        f"Schema version : "
        f"{metadata.get('schemaVersion')}"
    )
    print(
        f"Sections       : "
        f"{len(resources)}"
    )
    print(
        f"Total resources: "
        f"{total_resources}"
    )
    print(
        f"Output         : "
        f"{OUTPUT_FILE}"
    )
    print("=========================================")


if __name__ == "__main__":
    main()
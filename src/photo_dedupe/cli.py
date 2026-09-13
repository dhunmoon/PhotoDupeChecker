from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .dedupe import (
    collect_duplicates,
    find_duplicates,
    remove_duplicates,
    scan_folder,
)


def print_duplicates(
    duplicate_groups: list[dict],
) -> None:

    if not duplicate_groups:

        print("\nNo duplicates found.")
        return

    print()
    print("=" * 70)
    print(
        f"DUPLICATES FOUND: "
        f"{len(duplicate_groups)}"
    )
    print("=" * 70)

    for index, group in enumerate(
        duplicate_groups,
        start=1,
    ):

        print()
        print(
            f"Group {index} "
            f"[{group['type']}]"
        )

        print("  SOURCE 1:")
        print(
            f"    {group['source1']['path']}"
        )

        print("  SOURCE 2:")

        for image in group["source2"]:
            print(
                f"    {image['path']}"
            )

    print()
    print("=" * 70)


def compare(
    source1: str,
    source2: str,
    remove: int | None = None,
    collect: bool = False,
) -> int:

    source1_path = (
        Path(source1)
        .expanduser()
        .resolve()
    )

    source2_path = (
        Path(source2)
        .expanduser()
        .resolve()
    )

    if not source1_path.is_dir():

        print(
            f"ERROR: Source 1 does not exist: "
            f"{source1_path}",
            file=sys.stderr,
        )

        return 1

    if not source2_path.is_dir():

        print(
            f"ERROR: Source 2 does not exist: "
            f"{source2_path}",
            file=sys.stderr,
        )

        return 1

    if source1_path == source2_path:

        print(
            "ERROR: Source 1 and Source 2 "
            "cannot be the same folder.",
            file=sys.stderr,
        )

        return 1

    print(f"\nScanning source 1:")
    print(f"  {source1_path}")

    source1_images = scan_folder(
        source1_path,
        verbose=True,
    )

    print(
        f"Found {len(source1_images)} images."
    )

    print(f"\nScanning source 2:")
    print(f"  {source2_path}")

    source2_images = scan_folder(
        source2_path,
        verbose=True,
    )

    print(
        f"Found {len(source2_images)} images."
    )

    print("\nComparing images...")

    duplicate_groups = find_duplicates(
        source1_images,
        source2_images,
    )

    print_duplicates(
        duplicate_groups
    )

    if not duplicate_groups:
        return 0

    # --------------------------------------------------
    # Remove
    # --------------------------------------------------

    if remove is not None:

        print()
        print(
            f"WARNING: This will permanently "
            f"delete duplicates from source {remove}."
        )

        answer = input(
            "Continue? [y/N]: "
        ).strip().lower()

        if answer != "y":

            print("Cancelled.")
            return 0

        try:

            removed = remove_duplicates(
                duplicate_groups,
                remove,
            )

            print(
                f"\nRemoved {removed} files."
            )

        except OSError as error:

            print(
                f"ERROR: Could not remove file: "
                f"{error}",
                file=sys.stderr,
            )

            return 1

    # --------------------------------------------------
    # Collect
    # --------------------------------------------------

    elif collect:

        output = collect_duplicates(
            duplicate_groups,
            Path.cwd(),
        )

        print()
        print(
            f"Collected duplicates into:"
        )
        print(f"  {output}")

    return 0


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="photo-dedupe",
        description=(
            "Find duplicate and visually "
            "similar images."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two folders",
    )

    compare_parser.add_argument(
        "source1",
        help="First source folder",
    )

    compare_parser.add_argument(
        "source2",
        help="Second source folder",
    )

    compare_parser.add_argument(
        "--remove",
        type=int,
        choices=[1, 2],
        help=(
            "Remove duplicates from "
            "source 1 or source 2"
        ),
    )

    compare_parser.add_argument(
        "--collect",
        action="store_true",
        help=(
            "Collect duplicate groups "
            "into a timestamped folder"
        ),
    )

    return parser


def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if (
        args.command == "compare"
        and args.remove is not None
        and args.collect
    ):

        parser.error(
            "--remove and --collect "
            "cannot be used together"
        )

    if args.command == "compare":

        return compare(
            args.source1,
            args.source2,
            remove=args.remove,
            collect=args.collect,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
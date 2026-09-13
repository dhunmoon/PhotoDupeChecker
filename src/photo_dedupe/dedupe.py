from __future__ import annotations

import hashlib
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PIL import Image
import imagehash


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".bmp",
    ".tif",
    ".tiff",
}

PHASH_THRESHOLD = 6


def is_image(path: Path) -> bool:
    """Return True if the path looks like a supported image file."""
    return (
        path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def find_images(folder: Path) -> list[Path]:
    """Recursively find supported images inside a folder."""
    return [
        path
        for path in folder.rglob("*")
        if is_image(path)
    ]


def sha256_file(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Calculate SHA-256 for a file."""

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()


def perceptual_hash(path: Path) -> str | None:
    """
    Calculate a perceptual hash.

    Returns None if the image cannot be opened.
    """

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            return str(imagehash.phash(image))

    except Exception:
        return None


def scan_folder(
    folder: Path,
    verbose: bool = False,
) -> list[dict]:
    """
    Scan a folder and return information about each image.
    """

    folder = folder.resolve()

    images = []

    for path in find_images(folder):

        try:
            sha256 = sha256_file(path)
            phash = perceptual_hash(path)

            if phash is None:
                if verbose:
                    print(f"WARNING: Could not read image: {path}")

                continue

            images.append(
                {
                    "path": path,
                    "relative": path.relative_to(folder),
                    "size": path.stat().st_size,
                    "sha256": sha256,
                    "phash": phash,
                }
            )

        except (OSError, ValueError) as error:

            if verbose:
                print(
                    f"WARNING: Could not process "
                    f"{path}: {error}"
                )

    return images


def hamming_distance(
    hash1: str,
    hash2: str,
) -> int:
    """Calculate perceptual hash distance."""

    first = imagehash.hex_to_hash(hash1)
    second = imagehash.hex_to_hash(hash2)

    return first - second


def find_duplicates(
    source1_images: list[dict],
    source2_images: list[dict],
    phash_threshold: int = PHASH_THRESHOLD,
) -> list[dict]:
    """
    Find duplicates between two image collections.

    Exact duplicates are identified using SHA-256.

    Visual duplicates are identified using perceptual
    hash distance.
    """

    # Index source2 by SHA-256.
    exact_index = defaultdict(list)

    for image in source2_images:
        exact_index[image["sha256"]].append(image)

    duplicate_groups = []

    for image1 in source1_images:

        # --------------------------------------------------
        # Exact duplicate
        # --------------------------------------------------

        exact_matches = exact_index.get(
            image1["sha256"],
            [],
        )

        if exact_matches:

            duplicate_groups.append(
                {
                    "type": "exact",
                    "source1": image1,
                    "source2": exact_matches,
                }
            )

            continue

        # --------------------------------------------------
        # Visual duplicate
        # --------------------------------------------------

        visual_matches = []

        for image2 in source2_images:

            distance = hamming_distance(
                image1["phash"],
                image2["phash"],
            )

            if distance <= phash_threshold:
                visual_matches.append(
                    {
                        "image": image2,
                        "distance": distance,
                    }
                )

        if visual_matches:

            visual_matches.sort(
                key=lambda item: item["distance"]
            )

            duplicate_groups.append(
                {
                    "type": "visual",
                    "source1": image1,
                    "source2": [
                        item["image"]
                        for item in visual_matches
                    ],
                }
            )

    return duplicate_groups


def collect_duplicates(
    duplicate_groups: list[dict],
    output_parent: Path,
) -> Path:
    """
    Copy duplicate groups into a timestamped directory.

    Returns the created directory.
    """

    timestamp = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )

    output = (
        output_parent
        / f"duplicate-{timestamp}"
    )

    output.mkdir(
        parents=True,
        exist_ok=False,
    )

    for index, group in enumerate(
        duplicate_groups,
        start=1,
    ):

        group_dir = (
            output
            / f"group-{index:04d}"
        )

        source1_dir = group_dir / "source1"
        source2_dir = group_dir / "source2"

        source1_dir.mkdir(parents=True)
        source2_dir.mkdir(parents=True)

        # Source 1
        image1 = group["source1"]

        shutil.copy2(
            image1["path"],
            source1_dir / image1["path"].name,
        )

        # Source 2
        for image2 in group["source2"]:

            destination = (
                source2_dir
                / image2["path"].name
            )

            # Handle filename collision.
            if destination.exists():

                stem = destination.stem
                suffix = destination.suffix
                counter = 2

                while destination.exists():

                    destination = (
                        source2_dir
                        / f"{stem}-{counter}{suffix}"
                    )

                    counter += 1

            shutil.copy2(
                image2["path"],
                destination,
            )

    return output


def remove_duplicates(
    duplicate_groups: list[dict],
    source_number: int,
) -> int:
    """
    Remove duplicate files from source 1 or source 2.

    Returns the number of files removed.
    """

    if source_number not in (1, 2):
        raise ValueError(
            "source_number must be 1 or 2"
        )

    removed = 0

    for group in duplicate_groups:

        if source_number == 1:

            path = group["source1"]["path"]

            path.unlink()
            removed += 1

        else:

            for image in group["source2"]:

                image["path"].unlink()
                removed += 1

    return removed
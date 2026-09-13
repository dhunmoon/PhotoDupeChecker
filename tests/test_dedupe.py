from pathlib import Path

from PIL import Image

from photo_dedupe.dedupe import (
    collect_duplicates,
    find_duplicates,
    remove_duplicates,
    scan_folder,
)


def create_image(
    path: Path,
    size=(100, 100),
    color=(255, 0, 0),
):
    image = Image.new(
        "RGB",
        size,
        color,
    )

    image.save(path)


def test_scan_folder(tmp_path):

    folder = tmp_path / "photos"
    folder.mkdir()

    create_image(
        folder / "one.jpg",
    )

    create_image(
        folder / "two.jpg",
        color=(0, 255, 0),
    )

    # Non-image file.
    (folder / "notes.txt").write_text(
        "not an image"
    )

    images = scan_folder(folder)

    assert len(images) == 2


def test_exact_duplicate(tmp_path):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    create_image(
        source1 / "original.jpg",
        color=(255, 0, 0),
    )

    # Copy the exact same bytes.
    original_bytes = (
        source1 / "original.jpg"
    ).read_bytes()

    (
        source2 / "different-name.jpg"
    ).write_bytes(original_bytes)

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    assert len(duplicates) == 1

    group = duplicates[0]

    assert group["type"] == "exact"

    assert (
        group["source1"]["path"].name
        == "original.jpg"
    )

    assert (
        group["source2"][0]["path"].name
        == "different-name.jpg"
    )


def test_visual_duplicate(tmp_path):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    # Same visual content but different resolution.
    create_image(
        source1 / "small.jpg",
        size=(100, 100),
        color=(255, 0, 0),
    )

    create_image(
        source2 / "large.jpg",
        size=(500, 500),
        color=(255, 0, 0),
    )

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    assert len(duplicates) == 1

    assert duplicates[0]["type"] in {
        "exact",
        "visual",
    }


def test_unique_images_are_not_duplicates(
    tmp_path,
):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    create_image(
        source1 / "red.jpg",
        color=(255, 0, 0),
    )

    create_image(
        source2 / "blue.jpg",
        color=(0, 0, 255),
    )

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    assert len(duplicates) == 0


def test_collect_duplicates(tmp_path):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    create_image(
        source1 / "photo1.jpg",
        color=(255, 0, 0),
    )

    original_bytes = (
        source1 / "photo1.jpg"
    ).read_bytes()

    (
        source2 / "copy.jpg"
    ).write_bytes(original_bytes)

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    output = collect_duplicates(
        duplicates,
        tmp_path,
    )

    assert output.exists()
    assert output.is_dir()

    group = output / "group-0001"

    assert group.exists()

    assert (
        group
        / "source1"
        / "photo1.jpg"
    ).exists()

    assert (
        group
        / "source2"
        / "copy.jpg"
    ).exists()


def test_remove_source1(tmp_path):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    create_image(
        source1 / "photo.jpg",
    )

    original_bytes = (
        source1 / "photo.jpg"
    ).read_bytes()

    (
        source2 / "copy.jpg"
    ).write_bytes(original_bytes)

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    removed = remove_duplicates(
        duplicates,
        1,
    )

    assert removed == 1

    assert not (
        source1 / "photo.jpg"
    ).exists()

    assert (
        source2 / "copy.jpg"
    ).exists()


def test_remove_source2(tmp_path):

    source1 = tmp_path / "source1"
    source2 = tmp_path / "source2"

    source1.mkdir()
    source2.mkdir()

    create_image(
        source1 / "photo.jpg",
    )

    original_bytes = (
        source1 / "photo.jpg"
    ).read_bytes()

    (
        source2 / "copy.jpg"
    ).write_bytes(original_bytes)

    images1 = scan_folder(source1)
    images2 = scan_folder(source2)

    duplicates = find_duplicates(
        images1,
        images2,
    )

    removed = remove_duplicates(
        duplicates,
        2,
    )

    assert removed == 1

    assert (
        source1 / "photo.jpg"
    ).exists()

    assert not (
        source2 / "copy.jpg"
    ).exists()
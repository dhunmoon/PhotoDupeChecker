# Photo Dedupe

A Python CLI tool for finding duplicate and visually similar images across folders.

The tool is designed to help identify duplicate photos from sources such as:

* Phone backups
* Google Drive exports
* External hard drives
* Backup folders
* Multiple photo collections

The initial version supports comparing two folders and optionally removing or collecting duplicate files.

---

## Features

* Compare two folders recursively
* Detect exact duplicates using SHA-256
* Detect visually similar images using perceptual hashing
* Display duplicate groups and their file paths
* Remove duplicates from either source
* Collect duplicates into a timestamped folder
* Preserve duplicate groups when collecting
* Automated test suite using `pytest`

---

# Project Structure

```text
PhotoDupeChecker/
│
├── pyproject.toml
├── README.md
│
├── src/
│   └── photo_dedupe/
│       ├── __init__.py
│       ├── cli.py
│       └── dedupe.py
│
└── tests/
    └── test_dedupe.py
```

---

# Requirements

## Python

Python 3.10 or newer.

Check your Python version:

```bash
python --version
```

or:

```bash
python3 --version
```

Example:

```text
Python 3.14.4
```

---

# Setup

## 1. Clone or create the project

Go to the project directory:

```bash
cd ~/Documents/Projects/PhotoDupeChecker
```

---

## 2. Create a virtual environment

Create the virtual environment:

```bash
python3 -m venv .venv
```

---

## 3. Activate the virtual environment

Linux/macOS:

```bash
source .venv/bin/activate
```

You should see something similar to:

```text
(.venv) user@computer:PhotoDupeChecker$
```

### Deactivate

When finished working:

```bash
deactivate
```

---

# Install the Application

With the virtual environment activated:

```bash
pip install -e ".[test]"
```

The `-e` option installs the project in editable mode.

This means changes made to the source code are immediately available without reinstalling the package.

The `[test]` part also installs the development testing dependency:

```text
pytest
```

---

# Verify Installation

Check that the CLI is available:

```bash
photo-dedupe --help
```

You should see something similar to:

```text
usage: photo-dedupe [-h] {compare} ...

Find duplicate and visually similar images.

positional arguments:
  {compare}
    compare    Compare two folders
```

You can also check:

```bash
photo-dedupe compare --help
```

---

# Running Tests

Run the complete test suite:

```bash
pytest
```

A successful run should look similar to:

```text
============================= test session starts =============================
collected 7 items

tests/test_dedupe.py .......                                             [100%]

============================== 7 passed ======================================
```

Run tests with more detailed output:

```bash
pytest -v
```

---

# Running the Application

## Compare Two Folders

Basic command:

```bash
photo-dedupe compare <source1> <source2>
```

Example:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive
```

The application scans both folders recursively and displays duplicate groups.

---

# Example Output

```text
Scanning source 1:
  /home/user/Pictures/Phone

Found 1523 images.

Scanning source 2:
  /home/user/Pictures/GoogleDrive

Found 2876 images.

Comparing images...

======================================================================
DUPLICATES FOUND: 12
======================================================================

Group 1 [exact]
  SOURCE 1:
    /home/user/Pictures/Phone/IMG_1234.jpg

  SOURCE 2:
    /home/user/Pictures/GoogleDrive/holiday.jpg

Group 2 [visual]
  SOURCE 1:
    /home/user/Pictures/Phone/IMG_5678.jpg

  SOURCE 2:
    /home/user/Pictures/GoogleDrive/Trip/photo.jpg

======================================================================
```

---

# Duplicate Detection

The application currently uses two methods.

## 1. Exact Duplicate Detection

Files are hashed using SHA-256.

If two files have the same SHA-256 hash, they contain exactly the same bytes.

For example:

```text
IMG_1234.jpg
holiday.jpg
```

may have completely different filenames but still have:

```text
SHA-256:
abc123...
```

Therefore they are considered exact duplicates.

---

## 2. Visual Duplicate Detection

Images that are not byte-for-byte identical can still represent the same photograph.

For example:

```text
original.jpg
```

could be:

* Resized
* Recompressed
* Saved with different JPEG quality
* Renamed
* Converted between supported formats

For these cases the application calculates a perceptual hash (pHash).

Images with sufficiently similar perceptual hashes are treated as visual duplicate candidates.

> Note: The visual similarity algorithm is still being refined. In particular, simple images can sometimes produce false positives. The current test suite has already identified one such case, so the detection algorithm will be improved before relying on it for large-scale deletion.

---

# Supported Image Formats

The current implementation supports:

```text
.jpg
.jpeg
.png
.webp
.heic
.heif
.bmp
.tif
.tiff
```

The extensions are defined in:

```text
src/photo_dedupe/dedupe.py
```

---

# Remove Duplicates

By default, `compare` does **not modify anything**.

To remove duplicates from source 1:

```bash
photo-dedupe compare <source1> <source2> --remove 1
```

Example:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --remove 1
```

This means:

```text
Source 1 → duplicate files will be deleted
Source 2 → duplicate files will be kept
```

---

## Remove Duplicates From Source 2

```bash
photo-dedupe compare <source1> <source2> --remove 2
```

Example:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --remove 2
```

This means:

```text
Source 1 → duplicate files will be kept
Source 2 → duplicate files will be deleted
```

---

## Deletion Confirmation

The application asks for confirmation before deleting files:

```text
WARNING: This will permanently delete duplicates from source 1.

Continue? [y/N]:
```

Only entering:

```text
y
```

continues the deletion.

Anything else cancels the operation.

---

# Collect Duplicates

Instead of deleting duplicates, they can be copied into a separate timestamped folder.

Use:

```bash
photo-dedupe compare <source1> <source2> --collect
```

Example:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --collect
```

The application creates a directory similar to:

```text
duplicate-2026-09-13-16-58-32/
```

Inside it:

```text
duplicate-2026-09-13-16-58-32/
│
├── group-0001/
│   ├── source1/
│   │   └── IMG_1234.jpg
│   │
│   └── source2/
│       └── holiday.jpg
│
├── group-0002/
│   ├── source1/
│   │   └── IMG_5678.jpg
│   │
│   └── source2/
│       └── photo.jpg
│
└── group-0003/
    ├── source1/
    │   └── IMG_9012.jpg
    │
    └── source2/
        └── copy.jpg
```

The collection is created in the current working directory.

---

# Important Safety Rule

The safest workflow is:

### Step 1 — Compare

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive
```

Review the results.

### Step 2 — Collect

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --collect
```

Review the collected files.

### Step 3 — Delete

Only after verifying that the duplicate detection is correct:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --remove 1
```

or:

```bash
photo-dedupe compare ~/Pictures/Phone ~/Pictures/GoogleDrive --remove 2
```

Do not use `--remove` on an important photo collection until the visual matching algorithm has been sufficiently tested.

---

# Development

## Activate Environment

Every time you open a new terminal:

```bash
cd ~/Documents/Projects/PhotoDupeChecker
source .venv/bin/activate
```

---

## Install Changes

Because the project is installed in editable mode:

```bash
pip install -e ".[test]"
```

usually only needs to be run again when dependencies or project configuration change.

Changes to:

```text
src/photo_dedupe/
```

are imm

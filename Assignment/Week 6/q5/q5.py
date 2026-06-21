"""Question 5 - The Horcrux Sweeper.

Walks a directory tree and neutralises Horcruxes: files whose extension is
exactly .hx and whose size is exactly 7 bytes. Each one is renamed from .hx to
.destroyed, and the sorted list of relative paths is returned.
"""

import os
import tempfile

HORCRUX_EXTENSION = ".hx"
NEUTRALISED_EXTENSION = ".destroyed"
HORCRUX_SIZE_BYTES = 7


def purge_horcruxes(root_path):
    neutralized_files = []

    for dirpath, _dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            _, extension = os.path.splitext(filename)
            if extension != HORCRUX_EXTENSION:
                continue

            full_path = os.path.join(dirpath, filename)
            if os.path.getsize(full_path) != HORCRUX_SIZE_BYTES:
                continue

            base_name, _ = os.path.splitext(full_path)
            new_full_path = base_name + NEUTRALISED_EXTENSION
            os.rename(full_path, new_full_path)
            neutralized_files.append(os.path.relpath(new_full_path, root_path))

    return sorted(neutralized_files)


def main():
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "england", "london"))
        os.makedirs(os.path.join(root, "scotland"))

        files = {
            os.path.join(root, "diary.hx"): b"1234567",
            os.path.join(root, "england", "ring.hx"): b"1234567",
            os.path.join(root, "england", "london", "cup.hx"): b"123",
            os.path.join(root, "scotland", "locket.hxl"): b"1234567",
            os.path.join(root, "scotland", "snake.hx"): b"1234567",
        }
        for path, content in files.items():
            with open(path, "wb") as handle:
                handle.write(content)

        for rel in purge_horcruxes(root):
            print(rel)


if __name__ == "__main__":
    main()

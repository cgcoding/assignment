#!/usr/bin/env python3
"""Stdlib-only .xlsx -> .csv converter (zipfile + xml.etree.ElementTree).

Reads the first worksheet of an .xlsx, resolves shared strings and inline
strings, preserves cell/column order (filling gaps from the cell `r` refs),
and writes CSV with CRLF line endings to match the spreadsheet-export record
separator the assignment expects.
"""
import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")


def col_to_index(col_letters):
    n = 0
    for ch in col_letters:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def load_shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings = []
    for si in root.findall(f"{MAIN_NS}si"):
        # A shared string is either a single <t> or a sequence of runs <r><t>.
        parts = [t.text or "" for t in si.iter(f"{MAIN_NS}t")]
        strings.append("".join(parts))
    return strings


def cell_value(cell, shared):
    t = cell.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in cell.iter(f"{MAIN_NS}t"))
    v = cell.find(f"{MAIN_NS}v")
    if v is None or v.text is None:
        return ""
    if t == "s":
        return shared[int(v.text)]
    if t in (None, "n"):
        # Numeric cell: render whole numbers without a trailing ".0" so that
        # e.g. a year of 2019 and credits of 6 match the reference output.
        try:
            f = float(v.text)
        except ValueError:
            return v.text
        return str(int(f)) if f.is_integer() else v.text
    return v.text


def convert(xlsx_path, csv_path):
    with zipfile.ZipFile(xlsx_path) as zf:
        shared = load_shared_strings(zf)
        root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        sheet_data = root.find(f"{MAIN_NS}sheetData")
        rows = []
        for row in sheet_data.findall(f"{MAIN_NS}row"):
            cells = {}
            max_idx = -1
            for cell in row.findall(f"{MAIN_NS}c"):
                ref = cell.get("r", "")
                m = CELL_RE.match(ref)
                idx = col_to_index(m.group(1)) if m else (max_idx + 1)
                cells[idx] = cell_value(cell, shared)
                if idx > max_idx:
                    max_idx = idx
            rows.append([cells.get(i, "") for i in range(max_idx + 1)])

    width = max((len(r) for r in rows), default=0)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\r\n")
        for r in rows:
            w.writerow(r + [""] * (width - len(r)))


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])

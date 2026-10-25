#!/usr/bin/env python3
"""Build the files of a utilities-only release from the SPMF sequence files and the
quantitative databases they were converted into.

    python tools/build_release.py --spmf DIR --databases DIR --out DIR --urls FILE [NAME ...]

  --spmf       the SPMF sequence files, saved as NAME.txt
  --databases  the released NAME_seq.txt and NAME_eui.txt
  --urls       a two-column TSV, name and the SPMF address of its file
  --out        receives NAME_qty.txt, NAME_eui.txt and SOURCES.tsv

NAME_qty.txt has one line per kept line of the SPMF file (see tools/assemble.py) holding the
quantities of its items in order, and nothing else: no item identifier and no separator. The
item identifiers of every NAME_seq.txt are checked against the SPMF file position by position,
and the database is refused when one differs, so a quantity file never pairs with the wrong
SPMF file. The release is then assembled back with tools/assemble.py and compared byte for byte
with the databases it came from.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble  # noqa: E402

ITEM = re.compile(r"(-?[0-9]+)\[([0-9]+)\]\Z")


def quantities(name, spmf_path, seq_path, qty_path):
    with open(seq_path, "r", encoding="ascii", newline="\n") as sf, \
            open(qty_path, "w", encoding="ascii", newline="\n") as qf:
        for lineno, ids in enumerate(assemble.spmf_lines(spmf_path), 1):
            line = sf.readline()
            if line == "":
                raise SystemExit(f"{name}: {seq_path} ends before SPMF line {lineno}")
            got, qs = [], []
            for tok in line.split():
                m = ITEM.match(tok)
                if m:
                    got.append(int(m.group(1)))
                    qs.append(m.group(2))
                else:
                    got.append(int(tok))
            if got != ids:
                raise SystemExit(f"{name}: line {lineno} of {seq_path} does not carry the items of the SPMF file")
            qf.write(" ".join(qs) + "\n")
        if sf.readline() != "":
            raise SystemExit(f"{name}: {seq_path} has more lines than the SPMF file")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spmf", required=True)
    ap.add_argument("--databases", required=True)
    ap.add_argument("--urls", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args(argv)
    urls = {}
    with open(a.urls, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                n, u = line.rstrip("\n").split("\t")
                urls[n] = u
    names = a.names or list(urls)
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for name in names:
        spmf = os.path.join(a.spmf, name + ".txt")
        seq = os.path.join(a.databases, name + "_seq.txt")
        eui = os.path.join(a.databases, name + "_eui.txt")
        quantities(name, spmf, seq, os.path.join(a.out, name + "_qty.txt"))
        shutil.copyfile(eui, os.path.join(a.out, name + "_eui.txt"))
        rows.append((name, urls[name], assemble.sha256(spmf), assemble.sha256(seq), assemble.sha256(eui)))
        print(f"{name}: quantities written")
    with open(os.path.join(a.out, "SOURCES.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("name\turl\tspmf_sha256\tseq_sha256\teui_sha256\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    # Round trip: assemble the release back and compare with the databases it came from.
    with tempfile.TemporaryDirectory() as tmp:
        failed = 0
        for name in names:
            problems = assemble.assemble_one(name, assemble.read_sources(a.out)[name], a.out, a.spmf, tmp)
            for p in problems:
                print("ROUND TRIP FAILED " + p, file=sys.stderr)
            failed += bool(problems)
        print(f"round trip: {len(names) - failed} of {len(names)} databases reassembled byte for byte")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

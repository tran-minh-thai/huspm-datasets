#!/usr/bin/env python3
"""Assemble the quantitative databases of this collection from the SPMF sequence files.

This collection does not distribute the SPMF sequences. A release carries only what was
generated here: the quantity of every item position (NAME_qty.txt), the unit profit of every
item (NAME_eui.txt), and SHA-256 checksums of the SPMF files and of the assembled files
(SOURCES.tsv). This script joins the two:

    python tools/assemble.py --release DIR --spmf DIR --out DIR [--download] [NAME ...]

  --release  directory holding SOURCES.tsv and the NAME_qty.txt / NAME_eui.txt files
  --spmf     directory holding the SPMF sequence files, saved as NAME.txt
  --download fetch missing SPMF files from the address in SOURCES.tsv first
  --out      where NAME_seq.txt and NAME_eui.txt are written

It stops with exit code 1, and writes nothing for that database, when an SPMF file differs from
the checksum in SOURCES.tsv, when its item positions do not match the quantity file, or when an
assembled file differs from its pinned checksum. Only the Python standard library is used.

The SPMF file is read by the rules of SPMF_Converter (convert-spmf-to-quantitative), which
produced the released databases: lines that are empty or start with '#' or '@' are skipped,
tokens are separated by whitespace, a token that is not an integer is ignored, a non-negative
integer is an item and a negative one a separator. Each item is written as "id[q] ", each
separator as "id ", and every kept line ends with a newline.
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.request

INT = re.compile(r"[+-]?[0-9]+\Z")
INT_MIN, INT_MAX = -2 ** 31, 2 ** 31 - 1


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def spmf_lines(path):
    """The token lines of an SPMF file, as SPMF_Converter reads them: one list of integers per
    kept line (possibly empty)."""
    with open(path, "r", encoding="ascii", newline=None) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "" or line.startswith("#") or line.startswith("@"):
                continue
            ids = []
            for tok in line.split():
                if not INT.match(tok):
                    continue
                v = int(tok)
                if INT_MIN <= v <= INT_MAX:
                    ids.append(v)
            yield ids


def read_sources(release_dir):
    """SOURCES.tsv: name, url, sha256 of the SPMF file, sha256 of NAME_seq.txt, of NAME_eui.txt."""
    rows = {}
    with open(os.path.join(release_dir, "SOURCES.tsv"), encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            r = dict(zip(header, line.rstrip("\n").split("\t")))
            rows[r["name"]] = r
    return rows


def assemble_one(name, src, release_dir, spmf_dir, out_dir):
    """Returns a list of problems; empty when NAME_seq.txt and NAME_eui.txt were written and match."""
    spmf = os.path.join(spmf_dir, name + ".txt")
    if not os.path.isfile(spmf):
        return [f"{name}: SPMF file {spmf} not found (use --download, or save {src['url']} as {name}.txt)"]
    have = sha256(spmf)
    if have != src["spmf_sha256"]:
        return [f"{name}: {spmf} has SHA-256 {have}, expected {src['spmf_sha256']}; "
                f"the SPMF file is not the one these quantities belong to"]
    qty_path = os.path.join(release_dir, name + "_qty.txt")
    seq_tmp = os.path.join(out_dir, name + "_seq.txt.part")
    problems = []
    with open(qty_path, "r", encoding="ascii", newline="\n") as qf, \
            open(seq_tmp, "w", encoding="ascii", newline="\n") as out:
        for lineno, ids in enumerate(spmf_lines(spmf), 1):
            qline = qf.readline()
            if qline == "":
                problems.append(f"{name}: quantity file ends before SPMF line {lineno}")
                break
            qs = qline.split()
            items = sum(1 for v in ids if v >= 0)
            if len(qs) != items:
                problems.append(f"{name}: kept line {lineno} has {items} items and {len(qs)} quantities")
                break
            k = 0
            parts = []
            for v in ids:
                if v >= 0:
                    parts.append(f"{v}[{qs[k]}] ")
                    k += 1
                else:
                    parts.append(f"{v} ")
            out.write("".join(parts) + "\n")
        else:
            if qf.readline() != "":
                problems.append(f"{name}: quantity file has more lines than the SPMF file")
    if problems:
        os.remove(seq_tmp)
        return problems
    seq_path = os.path.join(out_dir, name + "_seq.txt")
    os.replace(seq_tmp, seq_path)
    eui_path = os.path.join(out_dir, name + "_eui.txt")
    with open(os.path.join(release_dir, name + "_eui.txt"), "rb") as a, open(eui_path, "wb") as b:
        b.write(a.read())
    for path, key in ((seq_path, "seq_sha256"), (eui_path, "eui_sha256")):
        got = sha256(path)
        if got != src[key]:
            problems.append(f"{name}: {os.path.basename(path)} has SHA-256 {got}, expected {src[key]}")
    if problems:
        for path in (seq_path, eui_path):
            os.remove(path)
    return problems


def download(url, path):
    """Saves url to path through a temporary file. The SPMF server refuses the default client
    name of urllib (HTTP 403), so the request names this script instead."""
    req = urllib.request.Request(url, headers={"User-Agent": "huspm-datasets-assemble/2.0"})
    part = path + ".part"
    with urllib.request.urlopen(req, timeout=120) as r, open(part, "wb") as f:
        while True:
            block = r.read(1 << 20)
            if not block:
                break
            f.write(block)
    os.replace(part, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--release", required=True)
    ap.add_argument("--spmf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args(argv)
    sources = read_sources(a.release)
    names = a.names or list(sources)
    unknown = [n for n in names if n not in sources]
    if unknown:
        print(f"not in SOURCES.tsv: {', '.join(unknown)}", file=sys.stderr)
        return 1
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.spmf, exist_ok=True)
    failed = 0
    for name in names:
        src = sources[name]
        spmf = os.path.join(a.spmf, name + ".txt")
        if a.download and not os.path.isfile(spmf):
            print(f"{name}: downloading {src['url']}")
            try:
                download(src["url"], spmf)
            except OSError as e:
                failed += 1
                print(f"FAILED {name}: could not download {src['url']}: {e}", file=sys.stderr)
                continue
        problems = assemble_one(name, src, a.release, a.spmf, a.out)
        if problems:
            failed += 1
            for p in problems:
                print("FAILED " + p, file=sys.stderr)
        else:
            print(f"{name}: {name}_seq.txt and {name}_eui.txt written and verified")
    print(f"{len(names) - failed} of {len(names)} databases assembled and verified")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

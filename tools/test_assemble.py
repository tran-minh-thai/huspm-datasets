#!/usr/bin/env python3
"""Self-test of tools/assemble.py and tools/build_release.py on hand-built files.

    python tools/test_assemble.py

Every case states what must happen; the script exits with code 1 when one does not. The
refusal cases each break one thing (the SPMF file, a quantity, a line count, an item of a
database) and must be refused for that reason, with no database left behind.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assemble  # noqa: E402
import build_release  # noqa: E402

# An SPMF file with the cases SPMF_Converter treats specially: a comment, an '@' header, an
# empty line, a line of blanks (kept, written as an empty line), a stray token, a '+' sign,
# leading zeros, tabs and CRLF line ends.
SPMF = (b"# comment\r\n@CONVERTED_FROM_TEXT\r\n"
        b"1 2 -1 3 -1 -2\r\n"
        b"\r\n"
        b"   \r\n"
        b"007 x +5 -1\t-2\r\n"
        b"-2\r\n")
# What SPMF_Converter writes for it with the quantities below.
SEQ = ("1[2] 2[1] -1 3[7] -1 -2 \n"
       "\n"
       "7[3] 5[1] -1 -2 \n"
       "-2 \n")
EUI = "# itemID:profit, test\n1:5\n2:7\n3:1\n5:2\n7:9\n"
QTY = "2 1 7\n\n3 1\n\n"


def write(path, data):
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("ascii"))


def setup(tmp):
    spmf, dbs, rel, out = (os.path.join(tmp, d) for d in ("spmf", "dbs", "rel", "out"))
    for d in (spmf, dbs, out):
        os.makedirs(d)
    write(os.path.join(spmf, "T.txt"), SPMF)
    write(os.path.join(dbs, "T_seq.txt"), SEQ)
    write(os.path.join(dbs, "T_eui.txt"), EUI)
    write(os.path.join(tmp, "urls.tsv"), "T\thttps://example.org/T.txt\n")
    return spmf, dbs, rel, out


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            code = fn(*args)
        except SystemExit as e:
            code = e.code
    return code, buf.getvalue()


def run_cases():
    results = []

    def case(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    with tempfile.TemporaryDirectory() as tmp:
        spmf, dbs, rel, out = setup(tmp)
        code, msg = quiet(build_release.main, ["--spmf", spmf, "--databases", dbs, "--urls",
                                               os.path.join(tmp, "urls.tsv"), "--out", rel])
        case("build: release built and round trip passes", code == 0, msg)
        if not os.path.isfile(os.path.join(rel, "SOURCES.tsv")):
            return results
        case("build: quantity file holds quantities only, one line per kept SPMF line",
             open(os.path.join(rel, "T_qty.txt")).read() == QTY)
        code, msg = quiet(assemble.main, ["--release", rel, "--spmf", spmf, "--out", out])
        case("assemble: clean files are assembled", code == 0, msg)
        case("assemble: output is SPMF_Converter's output byte for byte",
             open(os.path.join(out, "T_seq.txt"), "rb").read() == SEQ.encode())

        def refused(label, reason, prepare):
            with tempfile.TemporaryDirectory() as t2:
                s2, r2, o2 = (os.path.join(t2, d) for d in ("spmf", "rel", "out"))
                shutil.copytree(spmf, s2)
                shutil.copytree(rel, r2)
                os.makedirs(o2)
                prepare(s2, r2)
                code, msg = quiet(assemble.main, ["--release", r2, "--spmf", s2, "--out", o2])
                left = os.listdir(o2)
                case(f"refuses: {label}", code == 1 and reason in msg and not left,
                     f"code {code}, files left {left}, message: {msg.strip()}")

        def edit(path, old, new):
            data = open(path, "rb").read()
            assert data.count(old) == 1, (path, old)
            write(path, data.replace(old, new))

        def keep_sha(s2, r2):
            # make SOURCES.tsv accept the edited SPMF file, so the later check has to catch it
            p = os.path.join(r2, "SOURCES.tsv")
            rows = open(p).read().split("\n")
            cols = rows[1].split("\t")
            cols[2] = assemble.sha256(os.path.join(s2, "T.txt"))
            rows[1] = "\t".join(cols)
            write(p, "\n".join(rows))

        refused("an SPMF file that differs from its checksum", "is not the one these quantities belong to",
                lambda s2, r2: edit(os.path.join(s2, "T.txt"), b"1 2 -1 3", b"1 2 -1 4"))
        refused("a line with one quantity missing", "has 3 items and 2 quantities",
                lambda s2, r2: edit(os.path.join(r2, "T_qty.txt"), b"2 1 7\n", b"2 1\n"))
        refused("a line with one quantity too many", "has 3 items and 4 quantities",
                lambda s2, r2: edit(os.path.join(r2, "T_qty.txt"), b"2 1 7\n", b"2 1 7 1\n"))
        refused("a changed quantity", "T_seq.txt has SHA-256",
                lambda s2, r2: edit(os.path.join(r2, "T_qty.txt"), b"3 1\n", b"3 2\n"))
        refused("a changed unit profit", "T_eui.txt has SHA-256",
                lambda s2, r2: edit(os.path.join(r2, "T_eui.txt"), b"7:9", b"7:8"))
        refused("an extra line in the quantity file", "more lines than the SPMF file",
                lambda s2, r2: write(os.path.join(r2, "T_qty.txt"), QTY + "1\n"))
        refused("a quantity file shorter than the SPMF file", "ends before SPMF line",
                lambda s2, r2: write(os.path.join(r2, "T_qty.txt"), "2 1 7\n"))
        refused("an SPMF file with an extra item, checksum adjusted", "has 4 items and 3 quantities",
                lambda s2, r2: (edit(os.path.join(s2, "T.txt"), b"1 2 -1 3 -1", b"1 2 -1 3 8 -1"),
                                keep_sha(s2, r2)))
        refused("a missing SPMF file", "not found", lambda s2, r2: os.remove(os.path.join(s2, "T.txt")))

        # --download: a source that cannot be fetched is reported for that database, not raised
        with tempfile.TemporaryDirectory() as t4:
            s4, r4, o4 = (os.path.join(t4, d) for d in ("spmf", "rel", "out"))
            shutil.copytree(rel, r4)
            p = os.path.join(r4, "SOURCES.tsv")
            write(p, open(p).read().replace("https://example.org/T.txt", "file:///nonexistent/huspm/T.txt"))
            code, msg = quiet(assemble.main, ["--release", r4, "--spmf", s4, "--out", o4, "--download"])
            case("refuses: a download that fails", code == 1 and "could not download" in msg
                 and not os.listdir(o4), f"code {code}, message: {msg.strip()}")

        # build_release refuses a database whose items differ from the SPMF file
        with tempfile.TemporaryDirectory() as t3:
            d3 = os.path.join(t3, "dbs")
            shutil.copytree(dbs, d3)
            edit(os.path.join(d3, "T_seq.txt"), b"3[7]", b"4[7]")
            code, msg = quiet(build_release.main, ["--spmf", spmf, "--databases", d3, "--urls",
                                                   os.path.join(tmp, "urls.tsv"), "--out", os.path.join(t3, "rel")])
            case("build refuses: a database whose items differ from the SPMF file",
                 code not in (0, None) and "does not carry the items" in str(code) + msg, f"{code} {msg}")
    return results


def main():
    results = run_cases()
    for name, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"))
    failed = sum(not ok for _, ok, _ in results)
    print(f"{len(results) - failed} of {len(results)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

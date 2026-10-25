# huspm-datasets

Quantitative sequence databases for high utility sequential pattern mining, shared across
several studies so that each one measures on exactly the same data.

The sequences come from the public [SPMF](https://www.philippe-fournier-viger.com/spmf/) dataset
collection, which carries no utilities. Internal quantities and external profits were generated
for them by `SPMF_Converter`
([convert-spmf-to-quantitative](https://github.com/tran-minh-thai/convert-spmf-to-quantitative)).

**This repository distributes only what was generated here, not the SPMF sequences.** A release
holds the quantity of every item position and the profit of every item; `tools/assemble.py` joins
them with the SPMF files, which you download from SPMF, and checks every file it reads and writes
against a pinned SHA-256.

## Getting the data

```bash
VERSION=v2.0.0-utilities
curl -fLO https://github.com/tran-minh-thai/huspm-datasets/releases/download/$VERSION/huspm-datasets-$VERSION.tar.gz
tar xzf huspm-datasets-$VERSION.tar.gz
cd huspm-datasets-$VERSION
python tools/assemble.py --release . --spmf spmf --out databases --download
```

`--download` fetches each missing SPMF file from the address in `SOURCES.tsv` into `spmf/`. Without
it, save the files there yourself under the names below. The script needs Python 3 and nothing
else. It stops with exit code 1, and leaves no file for that database, when:

- an SPMF file differs from its checksum;
- a line of an SPMF file does not have as many items as the quantity file has quantities;
- an assembled file differs from its checksum.

| Name | SPMF file | Sequences | Items | Avg. length | Items/event | Total utility |
|---|---|---:|---:|---:|---:|---:|
| SIGN | `SIGN.txt` | 730 | 267 | 52.00 | 1.00 | 1,796,483 |
| LEVIATHAN | `LEVIATHAN.txt` | 5,834 | 9,025 | 33.81 | 1.00 | 10,502,159 |
| FIFA | `FIFA.txt` | 20,450 | 2,990 | 36.24 | 1.00 | 42,781,841 |
| BIBLE | `BIBLE.txt` | 36,369 | 13,905 | 21.64 | 1.00 | 35,550,162 |
| C8T1S5I8N5K | `data.slen_8.tlen_1.seq.patlen_5.lit.patlen_8.nitems_5000_spmf.txt` | 47,133 | 68,240 | 18.83 | 7.97 | 47,416,411 |
| BMS1 | `BMS1_spmf.txt` | 59,601 | 497 | 2.51 | 1.00 | 7,229,030 |
| KOSARAK | `kosarak_sequences.txt` | 990,002 | 41,270 | 8.10 | 1.00 | 385,921,994 |

The last line of the C8T1S5I8N5K file is an empty sequence, so a loader that skips empty
sequences reads 47,132.

In six of the seven databases every event holds a single item, which is the usual shape of SPMF
sequence data. Only C8T1S5I8N5K, synthetic data from the IBM Quest generator with 7.97 items per
event on average (1 to 26), exercises algorithms that distinguish within-event from across-event extensions.

## What a release holds

| file | content |
|---|---|
| `NAME_qty.txt` | one line per kept line of the SPMF file, holding the quantities of its items in order; no item identifier and no separator |
| `NAME_eui.txt` | `itemID:profit`, one line per item; comment lines start with `#` |
| `SOURCES.tsv` | per database: the SPMF address, and the SHA-256 of the SPMF file, of `NAME_seq.txt` and of `NAME_eui.txt` |
| `tools/assemble.py` | joins the two and verifies; `tools/test_assemble.py` is its self-test, and `tools/build_release.py` builds a release from the SPMF files and the databases |

`SOURCES.tsv` is also attached to the release on its own. Take it from the **release you
fetched**, not from this branch, which always describes the latest release.

The SPMF file is read by the rules of `SPMF_Converter`:

- lines that are empty or start with `#` or `@` are skipped;
- a token that is not an integer is ignored;
- a non-negative integer is an item and a negative one a separator.

The assembled files are byte for byte the files `SPMF_Converter` writes:

```
NAME_seq.txt   item[quantity] item[quantity] -1 item[quantity] -1 -2
               -1 ends an event, -2 ends the sequence
NAME_eui.txt   itemID:profit
```

## Generation parameters

| | |
|---|---|
| Seed | 42, a fresh generator per input file |
| Internal quantity | 70% in [1,2], 20% in [3,5], 10% in [6,10] |
| External profit | log-normal, `exp(N(2.5, 1.0))`, rounded, clamped to [1, 1000] |

Running `SPMF_Converter` on the SPMF files gives the same bytes as `tools/assemble.py`, so the
release can be audited rather than taken on trust. This holds because the generator is seeded per
file rather than shared across a batch. Check that the `_eui` header the converter writes reads
`# itemID:profit, log-normal, seed 42`; a converter that writes a different header is a different
version.

## Converting a dataset of your own

```bash
git clone https://github.com/tran-minh-thai/convert-spmf-to-quantitative
cd convert-spmf-to-quantitative
javac -encoding UTF-8 -d out src/SPMF_Converter.java
java -cp out SPMF_Converter YOUR_DATASET.txt      # raw file in datasets/
```

A study that converts its own data stays reproducible if it:

1. **seeds the generator per file, not per batch**, so that the bytes a file receives do not
   depend on which other files were converted before it;
2. **records checksums next to whatever consumes the data**, so that a later change to the shared
   data cannot silently change the numbers;
3. **names a release after what produced it** rather than after a counter;
4. **states the generation parameters in the paper**: seed, the distribution of internal
   quantities and that of external profits.

## Earlier releases

Releases `v1-seed42-lognormal` to `v1.2.1-measured-quantity` attached the complete databases,
SPMF sequences included. Their archives have been withdrawn; each release keeps its
`MANIFEST.sha256`, and `v2.0.0-utilities` reproduces the 14 files of the seven SPMF databases byte
for byte, so a study pinned to one of them can assemble the same bytes and check them against that
manifest. `ONLINE_RETAIL_II_ALL` and `ONLINE_RETAIL_II_QTY`, built from
[UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (CC BY 4.0), are
attached as separate files to `v1.2.1-measured-quantity`.

## Licence and attribution

CC BY 4.0 for what originates here: the generated quantities and profits, the parameter choices,
the checksums, the scripts, and the arrangement of the collection. See `LICENSE` and
`CITATION.cff`. The SPMF sequences are not distributed here, and the rights in them stay with their
original holders. Reusers should credit both this repository and SPMF.

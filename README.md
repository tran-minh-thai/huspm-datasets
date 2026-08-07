# huspm-datasets

Quantitative sequence databases for high utility sequential pattern mining, shared across
several studies so that each one measures on exactly the same data.

The sequence structure comes from the public [SPMF](https://www.philippe-fournier-viger.com/spmf/)
datasets, which carry no utilities. Internal quantities and external profits are generated
by `SPMF_Converter`, distributed with
[convert-spmf-to-quantitative](https://github.com/tran-minh-thai/convert-spmf-to-quantitative).

## Licence and attribution

The generated utilities, the parameter choices, the manifests and the arrangement of the
released collection are licensed CC BY 4.0. The underlying sequence structure comes from the
public [SPMF](https://www.philippe-fournier-viger.com/spmf/) collection and is redistributed
unchanged; rights in that material stay with its original holders. Reusers should credit both.
See `LICENSE` and `CITATION.cff`.

## Getting the data

The databases are attached to a release rather than tracked in git, so cloning this
repository stays fast and updating the data does not grow its history.

```bash
VERSION=v1.1-seed42-lognormal
curl -fLO https://github.com/tran-minh-thai/huspm-datasets/releases/download/$VERSION/huspm-datasets-$VERSION.tar.gz
tar xzf huspm-datasets-$VERSION.tar.gz
shasum -a 256 -c MANIFEST.sha256        # Linux: sha256sum -c MANIFEST.sha256
```

Each release is named after the parameters that produced it. A study needing a different
seed or a different utility distribution pins a different release instead of overwriting
this one, so results published against an older release stay reproducible.

## Contents of `v1.1-seed42-lognormal`

Two files per dataset: `NAME_seq.txt` holds the sequences with quantities, `NAME_eui.txt`
holds one profit per item.

| Dataset | Sequences | Items | Avg. length | Items/event | Total utility |
|---|---:|---:|---:|---:|---:|
| SIGN | 730 | 267 | 52.00 | 1.00 | 1,796,483 |
| LEVIATHAN | 5,834 | 9,025 | 33.81 | 1.00 | 10,502,159 |
| FIFA | 20,450 | 2,990 | 36.24 | 1.00 | 42,781,841 |
| BIBLE | 36,369 | 13,905 | 21.64 | 1.00 | 35,550,162 |
| C8T1S5I8N5K | 47,133 | 68,240 | 18.83 | 7.97 | 47,416,411 |
| BMS1 | 59,601 | 497 | 2.51 | 1.00 | 7,229,030 |
| KOSARAK | 990,002 | 41,270 | 8.10 | 1.00 | 385,921,994 |
| ONLINE_RETAIL_II_ALL | 4,383 | 41,431 | 122.06 | 22.78 | 29,545,643 |

Note the items-per-event column: in six of the eight datasets every event holds a single
item, which is the usual shape of SPMF sequence data. Only C8T1S5I8N5K and
ONLINE_RETAIL_II_ALL exercise algorithms that distinguish within-event from across-event
extensions, and they do so from opposite directions: C8T1S5I8N5K is synthetic with events of
five to ten items, while ONLINE_RETAIL_II_ALL is real retail with baskets averaging 22.78
items over sequences of only about five events. A suite drawn from the other six measures
across-event extension alone.

`v1.1` adds ONLINE_RETAIL_II_ALL and changes nothing else: the fourteen files of `v1` are
byte-identical in both releases, so a study pinned to `v1` can move to `v1.1` without
remeasuring.

## Generation parameters

| | |
|---|---|
| Seed | 42 |
| Internal quantity | 70% in [1,2], 20% in [3,5], 10% in [6,10] |
| External profit | log-normal, `exp(N(2.5, 1.0))`, rounded, clamped to [1, 1000] |

## Rebuilding instead of downloading

The conversion is deterministic **provided the generator is seeded per input file rather than
shared across a batch**. With per-file seeding a given raw file converts to the same bytes on
any machine, whether it is converted alone or alongside others; with one generator shared
across the batch, the output depends on which files were converted and in what order, and the
checksums below will not match.

These releases were produced with the per-file version. Check before rebuilding: the converter
must create its `Random` inside the per-file routine, not hold it as a static field, and the
`_eui` header it writes must read `# itemID:profit, log-normal, seed 42`. A copy that writes a
different header is a different version and will not reproduce these bytes.

Download the raw files from SPMF, then:

```bash
java -cp out SPMF_Converter          # expects the raw .txt files in datasets/
shasum -a 256 -c MANIFEST.sha256
```

This is the fallback when the release is unreachable, and it is also how these files can be
audited rather than taken on trust.

## Converting a dataset of your own

The converter is
[convert-spmf-to-quantitative](https://github.com/tran-minh-thai/convert-spmf-to-quantitative).
Any SPMF sequence file can be turned into a quantitative database with it, and a study that
follows the four points below is reproducible in the same way these releases are.

```bash
git clone https://github.com/tran-minh-thai/convert-spmf-to-quantitative
cd convert-spmf-to-quantitative
javac -encoding UTF-8 -d out src/SPMF_Converter.java
java -cp out SPMF_Converter YOUR_DATASET.txt      # raw file in datasets/
```

**1. Seed the generator per file, not per batch.** This is the whole of what makes the output
reproducible. With one generator shared across a run, the bytes a file receives depend on
which other files were converted before it, and that ordering is not recorded anywhere.

**2. Record checksums next to whatever consumes the data.** A manifest of SHA-256 sums,
committed in the study that uses the files, is what pins the version. Without it a later
change to the shared data silently produces numbers that no longer match what was published.

**3. Name the release after the parameters that produced it,** not after a version counter.
`v1.1-seed42-lognormal` says what is inside; `v2` does not. A study needing a different seed
or distribution then pins a different release rather than overwriting one that published
results depend on.

**4. State the generation parameters in the paper,** not only in the repository: seed, the
distribution of internal quantities, and the distribution of external profits. They are what
another group needs in order to build an equivalent dataset from scratch.

Datasets converted this way are welcome here. Open an issue with the raw SPMF file name and
the checksums produced, and they can go into a following release.

The raw SPMF files are not redistributed here; download them from SPMF directly.

## File format

```
NAME_seq.txt   item[quantity] item[quantity] -1 item[quantity] -1 -2
               -1 ends an event, -2 ends the sequence

NAME_eui.txt   itemID:profit
               one line per item, comment lines start with #
```

# huspm-datasets

Quantitative sequence databases for high utility sequential pattern mining, shared across
several studies so that each one measures on exactly the same data.

The sequence structure comes from the public [SPMF](https://www.philippe-fournier-viger.com/spmf/)
datasets, which carry no utilities. Internal quantities and external profits are generated
by `SPMF_Converter`, distributed with
[rhuspm-miner](https://github.com/tran-minh-thai/rhuspm-miner).

## Getting the data

The databases are attached to a release rather than tracked in git, so cloning this
repository stays fast and updating the data does not grow its history.

```bash
VERSION=v1-seed42-lognormal
curl -fLO https://github.com/tran-minh-thai/huspm-datasets/releases/download/$VERSION/huspm-datasets-$VERSION.tar.gz
tar xzf huspm-datasets-$VERSION.tar.gz
shasum -a 256 -c MANIFEST.sha256        # Linux: sha256sum -c MANIFEST.sha256
```

Each release is named after the parameters that produced it. A study needing a different
seed or a different utility distribution pins a different release instead of overwriting
this one, so results published against an older release stay reproducible.

## Contents of `v1-seed42-lognormal`

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

Note the items-per-event column: in six of the seven datasets every event holds a single
item, which is the usual shape of SPMF sequence data. Algorithms that distinguish
within-event from across-event extensions are exercised only by C8T1S5I8N5K here.

## Generation parameters

| | |
|---|---|
| Seed | 42 |
| Internal quantity | 70% in [1,2], 20% in [3,5], 10% in [6,10] |
| External profit | log-normal, `exp(N(2.5, 1.0))`, rounded, clamped to [1, 1000] |

## Rebuilding instead of downloading

The conversion is deterministic. Its generator is seeded per input file rather than shared
across a batch, so a given raw file converts to the same bytes on any machine, whether it is
converted alone or alongside others. Download the raw files from SPMF, then:

```bash
java -cp out SPMF_Converter          # expects the raw .txt files in datasets/
shasum -a 256 -c MANIFEST.sha256
```

This is the fallback when the release is unreachable, and it is also how these files can be
audited rather than taken on trust.

The raw SPMF files are not redistributed here; download them from SPMF directly.

## File format

```
NAME_seq.txt   item[quantity] item[quantity] -1 item[quantity] -1 -2
               -1 ends an event, -2 ends the sequence

NAME_eui.txt   itemID:profit
               one line per item, comment lines start with #
```

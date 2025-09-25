# Phone Lookup

Bulk phone number lookup CLI backed by LMDB and the NPANXX/OCN datasets.

## Requirements

- Python 3.10+

## Data preparation

Extract the bundled data and import it into LMDB:

```bash
make import
```

The target unzips the CSV bundle, then executes `phone-lookup import`.

## CLI usage

Perform lookups by invoking the `lookup` subcommand:

```bash
phone-lookup lookup --file numbers.txt --output results.txt
```

Each lookup prints progress in the terminal and writes results in `number:LTYPE:CommonName` format to the output file.

Import or re-import data with the `import` subcommand:

```bash
phone-lookup import --npanxx-path data/raw/phoneplatinumwire.csv --ocn-path data/raw/ocn.csv
```

## Development

Create a virtualenv and install the project if you want to run the CLI directly on the host:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

For local execution without installation, run `python -m phone_lookup.cli <command> [...]` (ensure `PYTHONPATH=src`).

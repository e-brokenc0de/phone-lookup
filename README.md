# Phone Lookup

Bulk phone number lookup CLI backed by an LMDB database populated from the NPANXX/OCN datasets.

## Requirements

- Python 3.10+
- [python-lmdb](https://pypi.org/project/lmdb/) (installed automatically when you install this project)

## Data preparation

Extract the bundled data and import it into the LMDB database stored in `data/store`:

```bash
make import
```

The target unzips the CSV bundle (if necessary) and runs `phone-lookup import` using your local Python interpreter. The LMDB
environment is created automatically if it does not already exist.

## CLI usage

Perform lookups by invoking the `lookup` subcommand. The CLI reads from the LMDB environment stored at `data/store` by default;
override the path with `--database-path` if you keep the data elsewhere.

```bash
phone-lookup lookup --file numbers.txt --output results.txt
```

Each lookup prints progress in the terminal and writes results in `number:LTYPE:CommonName` format to the output file.

Import or re-import data with the `import` subcommand:

```bash
phone-lookup import --npanxx-path data/raw/phoneplatinumwire.csv --ocn-path data/raw/ocn.csv
```

Both commands accept `--database-path` to target a different LMDB directory.

## Development

Create a virtualenv and install the project if you want to run the CLI directly on the host:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

For local execution without installation, run `PYTHONPATH=src python -m phone_lookup.cli <command> [...]`.

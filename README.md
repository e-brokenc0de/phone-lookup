# Phone Lookup

Bulk phone number lookup CLI backed by Redis and the NPANXX/OCN datasets.

## Requirements

- Docker + Docker Compose plugin

## Data preparation

Extract the bundled data and import it into Redis:

```bash
make import
```

The target unzips the CSV bundle, ensures the Redis container is running, then executes `phone-lookup import` from an ephemeral Python container on the same Docker network.

## Running Redis manually

If you only need Redis without importing data, you can start it independently:

```bash
docker compose up -d redis
```

Redis is addressable as `redis:6379` from other Docker services and is exposed on `localhost:6379` for convenience.

## CLI usage

Perform lookups by invoking the `lookup` subcommand (defaults connect to the Docker Redis service):

```bash
phone-lookup lookup --file numbers.txt --output results.txt
```

Each lookup prints progress in the terminal and writes results in `number:LTYPE:CommonName` format to the output file.

Import or re-import data with the `import` subcommand:

```bash
phone-lookup import --npanxx-path data/raw/phoneplatinumwire.csv --ocn-path data/raw/ocn.csv
```

Both subcommands connect to the Docker-hosted Redis by default; override the host and port only if you run Redis elsewhere.

## Development

Create a virtualenv and install the project if you want to run the CLI directly on the host:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

For local execution without installation, run `python -m phone_lookup.cli <command> [...]` (ensure `PYTHONPATH=src`).

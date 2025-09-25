.PHONY: setup import clean test bench

RAW_DIR := data/raw
DATA_ZIP := data/data.zip
DB_PATH ?= data/store
PYTHON ?= python3

setup:
	@mkdir -p $(RAW_DIR)
	@unzip -oq $(DATA_ZIP) -d $(RAW_DIR)

import: setup
	@PYTHONPATH=src $(PYTHON) -m phone_lookup.cli import --database-path $(DB_PATH) --npanxx-path $(RAW_DIR)/phoneplatinumwire.csv --ocn-path $(RAW_DIR)/ocn.csv

clean:
	@rm -f $(RAW_DIR)/*.csv $(RAW_DIR)/*.pdf $(RAW_DIR)/readme.txt

test:
	@PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -t .

bench:
	@PYTHONPATH=src $(PYTHON) benchmarks/benchmark_store.py

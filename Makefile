.PHONY: setup import clean

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

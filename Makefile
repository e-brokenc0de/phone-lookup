.PHONY: setup import clean

RAW_DIR := data/raw
DATA_ZIP := data/data.zip

setup:
	@mkdir -p $(RAW_DIR)
	@unzip -oq $(DATA_ZIP) -d $(RAW_DIR)

import: setup
	@phone-lookup import --npanxx-path $(RAW_DIR)/phoneplatinumwire.csv --ocn-path $(RAW_DIR)/ocn.csv

clean:
	@rm -f $(RAW_DIR)/*.csv $(RAW_DIR)/*.pdf $(RAW_DIR)/readme.txt data/prod.lmdb*

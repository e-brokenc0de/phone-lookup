.PHONY: setup import clean redis-up redis-down redis-logs

RAW_DIR := data/raw
DATA_ZIP := data/data.zip
COMPOSE ?= docker compose

setup:
	@mkdir -p $(RAW_DIR)
	@unzip -oq $(DATA_ZIP) -d $(RAW_DIR)

import: setup
	@$(COMPOSE) up -d redis
	@$(COMPOSE) run --rm cli "python -m pip install --no-cache-dir -e . && phone-lookup import --npanxx-path $(RAW_DIR)/phoneplatinumwire.csv --ocn-path $(RAW_DIR)/ocn.csv"

clean:
	@rm -f $(RAW_DIR)/*.csv $(RAW_DIR)/*.pdf $(RAW_DIR)/readme.txt

redis-up:
	@$(COMPOSE) up -d redis

redis-down:
	@$(COMPOSE) down

redis-logs:
	@$(COMPOSE) logs -f redis

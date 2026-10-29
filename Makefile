ETL ?= /Volumes/Element/Github2/etl
# owid/etl commit whose V-Dem code built the published charts (data/reference/owid_etl/PROVENANCE.json)
ETL_COMMIT := bac9e164b0b4a828474804727af503e0785717ff
OWID_LIBS := data/cache/owid-etl-$(ETL_COMMIT)
SNAPSHOTS := data/raw/owid-snapshots
CATALOG := data/raw/owid-catalog
DB := data/sqlite/vdem2026.db
CATALOG_TABLES := garden/demography/2024-07-15/population/population garden/regions/2023-01-01/regions/regions

.PHONY: data download build verify figure-lists tasks golden-env golden-pipeline golden-specs golden test

data: download build verify          ## Rebuild the SQLite database from OWID's V-Dem snapshot and catalog tables

download:                            ## Fetch the MD5-verified V-Dem v16 snapshot and OWID's population and region tables
	uv run python -m pipeline.download_snapshots $(ETL) $(SNAPSHOTS) democracy/2026-03-17
	uv run python -m pipeline.download_catalog $(CATALOG) $(CATALOG_TABLES)

build:                               ## Format-convert the snapshot and catalog tables into one SQLite database
	uv run python -m pipeline.build_sqlite $(SNAPSHOTS)/democracy/2026-03-17 $(CATALOG) $(DB)

verify:                              ## Check every table against recorded content fingerprints
	uv run python -m pipeline.verify_sqlite $(DB) data/manifests/BUILD.json

figure-lists:                        ## Select the V-Dem-only charts; list the figures of each page that shows one (network)
	uv run python -m scripts.select_charts docs/owid-mapping/mapping.json docs/owid-mapping/crawl.json data/reference/charts.json
	uv run python -m scripts.owid_pages data/reference/charts.json docs/owid-mapping/crawl.json scripts/articles

tasks:                               ## Capture OWID/: pages from scripts/articles/, then chart pages of the other charts (network)
	uv run python -m scripts.build_pages scripts/articles OWID
	uv run python -m scripts.build_chart_pages data/reference/charts.json OWID
	uv run python -m scripts.add_figure_sources OWID

golden-env:                          ## Environment for golden programs: OWID's libraries at ETL_COMMIT (needs an owid/etl clone)
	mkdir -p $(OWID_LIBS)
	git -C $(ETL) archive $(ETL_COMMIT) lib/catalog lib/datautils lib/repack | tar -x -C $(OWID_LIBS)
	uv venv --python 3.12 .venv-golden
	VIRTUAL_ENV=.venv-golden uv pip install -e $(OWID_LIBS)/lib/repack -e $(OWID_LIBS)/lib/datautils \
		-e $(OWID_LIBS)/lib/catalog pandas==3.0.6 numpy==2.4.4

golden-pipeline:                     ## Run OWID's V-Dem processing on the database (shared part of every golden program)
	.venv-golden/bin/python -m golden.vdem_pipeline --db $(DB) --out data/golden/vdem

golden-specs:                        ## Write each figure's spec: source columns, view settings, output precision
	uv run python -m scripts.write_golden_specs OWID

golden: golden-pipeline              ## Check every figure's golden program against OWID's published figure data
	uv run python -m scripts.run_golden OWID

test:
	uv run pytest -q

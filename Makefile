PYTHON ?= python
.PHONY: verify test figures replay qa
verify:
	$(PYTHON) TOOLS/check_reference.py
	$(PYTHON) REFERENCE_DATA/starlight-iris-2026/scripts/verify_all_results.py
	$(PYTHON) scripts/verify_release.py

test:
	$(PYTHON) -m pytest -q

figures:
	$(PYTHON) scripts/build_figures.py

replay:
	$(PYTHON) -m starlight replay all --out outputs

qa: verify test

#!/usr/bin/env python3
import runpy
import sys
sys.argv = ["genlens_digest.py", "--retry-only"]
runpy.run_path("/root/.hermes/profiles/genny/scripts/genlens_digest.py", run_name="__main__")

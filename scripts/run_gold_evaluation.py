#!/usr/bin/env python3
"""Thin wrapper for the Milestone 12 evaluation runner.

The real logic lives in `kendra_api.evaluation.run` (installed with `apps/api`) so it
ships as part of the package rather than as a standalone script with its own copy of
the dataset/scoring logic. See that module's docstring for usage.
"""

import sys

from kendra_api.evaluation.run import main

if __name__ == "__main__":
    sys.exit(main())

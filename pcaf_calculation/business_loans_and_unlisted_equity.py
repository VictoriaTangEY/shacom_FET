# Load packages
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict

from input_handler.load_parameters import (
    load_configuration_file,
    load_parameters,
)
from input_handler.env_setting import run_setting


def run_business_loans_and_unlisted_equity(rc, logger, instruments=None, param=None):
    logger.info("Starting calculation for business loans and unlisted equity")
    # TODO: implement financed emissions logic for this asset class.


import argparse
import json
from pathlib import Path

from input_handler import RunSetting, load_configuration_file, load_parameters
from util.loggers import createLogHandler
from main_calculation import (
    run_listed_equity_and_corporate_bonds,
    run_business_loans_and_unlisted_equity,
    run_project_finance,
    run_commercial_real_estate,
    run_mortgages,
    run_sovereign_debt,
)


def run_calculation(rc, logger, param=None):
    """
    Orchestrate financed emissions calculation for all asset classes.
    Each asset class has its own module under main_calculation.
    """
    logger.info("Starting main financed emissions calculation.")

    run_listed_equity_and_corporate_bonds(rc=rc, parent_logger=logger, param=param)
    run_business_loans_and_unlisted_equity(rc=rc, parent_logger=logger, param=param)
    run_project_finance(rc=rc, parent_logger=logger, param=param)
    run_commercial_real_estate(rc=rc, parent_logger=logger, param=param)
    run_mortgages(rc=rc, parent_logger=logger, param=param)
    run_sovereign_debt(rc=rc, parent_logger=logger, param=param)

    logger.info("Main financed emissions calculation complete.")


def main(run_config):
    c = run_config.copy()
    rc = RunSetting(run_config=c)

    rc.log_path.mkdir(parents=True, exist_ok=True)
    rc.result_path.mkdir(parents=True, exist_ok=True)
    rc.report_path.mkdir(parents=True, exist_ok=True)

    logger = createLogHandler("main", rc.log_path / "Log_file_main.log")
    logger.info("Run started. Config loaded.")

    param = {}
    if rc.param_path.exists():
        try:
            param = load_parameters(rc.param_path)
            logger.info("Parameters loaded.")
        except Exception as e:
            logger.exception("Parameter load failed: %s", e)

    try:
        run_calculation(rc=rc, logger=logger, param=param)
    except Exception as e:
        logger.exception("Calculation failed: %s", e)
        raise
    finally:
        logger.handlers.clear()

    logger = createLogHandler("main", rc.log_path / "Log_file_main.log")
    logger.info("Run finished.")
    logger.handlers.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--configPath", type=str, required=True, help="Path to run_config_file.json")
    args = parser.parse_args()

    with open(Path(args.configPath), "r", encoding="utf-8") as f:
        config = json.load(f)

    main(run_config=config)

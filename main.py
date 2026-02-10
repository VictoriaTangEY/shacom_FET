import argparse
import json
from pathlib import Path

from input_handler import RunSetting, load_configuration_file, load_parameters
from util.loggers import createLogHandler
from fe_calculation import (
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
    All detailed logs are written via the fe_calculation logger.
    """
    logger.info("Starting main financed emissions calculation.")

    run_listed_equity_and_corporate_bonds(rc=rc, logger=logger, param=param)
    run_business_loans_and_unlisted_equity(rc=rc, logger=logger, param=param)
    run_project_finance(rc=rc, logger=logger, param=param)
    run_commercial_real_estate(rc=rc, logger=logger, param=param)
    run_mortgages(rc=rc, logger=logger, param=param)
    run_sovereign_debt(rc=rc, logger=logger, param=param)

    logger.info("Main financed emissions calculation complete.")


def main(run_config):
    c = run_config.copy()
    rc = RunSetting(run_config=c)

    rc.log_path.mkdir(parents=True, exist_ok=True)
    rc.result_path.mkdir(parents=True, exist_ok=True)
    rc.report_path.mkdir(parents=True, exist_ok=True)

    main_logger = createLogHandler("main", rc.log_path / "Log_file_main.log")
    main_logger.info("Run started. Config loaded.")

    param = {}
    if rc.param_path.exists():
        try:
            param = load_parameters(rc.param_path)
            main_logger.info("Parameters loaded.")
        except Exception as e:
            main_logger.exception("Parameter load failed: %s", e)

    try:
        fe_logger = createLogHandler(
            "fe_calculation", rc.log_path / "Log_fe_calculation.log"
        )
        fe_logger.info("Initialized fe_calculation logger.")
        run_calculation(rc=rc, logger=fe_logger, param=param)
    except Exception as e:
        main_logger.exception("Calculation failed: %s", e)
        raise
    finally:
        main_logger.handlers.clear()

    main_logger = createLogHandler("main", rc.log_path / "Log_file_main.log")
    main_logger.info("Run finished.")
    main_logger.handlers.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--configPath", type=str, required=True, help="Path to run_config_file.json")
    args = parser.parse_args()

    with open(Path(args.configPath), "r", encoding="utf-8") as f:
        config = json.load(f)

    main(run_config=config)

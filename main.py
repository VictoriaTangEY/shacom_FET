import argparse
import json
from pathlib import Path

from input_handler import run_setting, load_parameters, DataPreprocessor
from util.loggers import createLogHandler
from pcaf_calculation import run_pcaf_all


def main(run_config):
    c = run_config.copy()
    rc = run_setting(run_config=c)
    rc.log_path.mkdir(parents=True, exist_ok=True)
    rc.result_path.mkdir(parents=True, exist_ok=True)
    rc.report_path.mkdir(parents=True, exist_ok=True)

    main_logger = createLogHandler("main", rc.log_path / "Log_file_main.log")
    main_logger.info("===================================================")
    main_logger.info("Start running...")

    param = {}
    if rc.param_path.exists():
        try:
            param = load_parameters(rc.param_path, logger=main_logger)
            main_logger.info("Parameters loaded successfully")
        except Exception as e:
            main_logger.exception("Parameter load failed: %s", e)

    fe_logger = createLogHandler(
        "pcaf_calculaton", rc.log_path / "Log_pcaf_calculaton.log"
    )
    fe_logger.info("Initialized pcaf_calculaton logger.")

    dp = DataPreprocessor(context=rc)
    try:
        splits = dp.load_and_split_instruments(logger=fe_logger)
        main_logger.info("Input data loaded successfully")
    except Exception as e:
        main_logger.exception("Input data load failed: %s", e)
        raise

    try:
        main_logger.info("Starting PCAF calculation")
        run_pcaf_all(rc=rc, logger=fe_logger, instruments_splits=splits, param=param)
        main_logger.info("PCAF calculation complete")
    except Exception as e:
        main_logger.exception("Calculation failed: %s", e)
        raise
    finally:
        fe_logger.handlers.clear()
        main_logger.handlers.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--configPath", type=str, required=True, help="Path to run_config_file.json")
    args = parser.parse_args()

    with open(Path(args.configPath), "r", encoding="utf-8") as f:
        config = json.load(f)

    main(run_config=config)

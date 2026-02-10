from util.loggers import createLogHandler


def run_commercial_real_estate(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Commercial real estate.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "commercial_real_estate",
        rc.log_path / "Log_commercial_real_estate.log",
    )

    logger.info("Starting calculation for commercial real estate.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for commercial real estate.")
        logger.handlers.clear()


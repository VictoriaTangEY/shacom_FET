from util.loggers import createLogHandler


def run_sovereign_debt(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Sovereign debt.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "sovereign_debt",
        rc.log_path / "Log_sovereign_debt.log",
    )

    logger.info("Starting calculation for sovereign debt.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for sovereign debt.")
        logger.handlers.clear()


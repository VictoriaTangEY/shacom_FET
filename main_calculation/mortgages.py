from util.loggers import createLogHandler


def run_mortgages(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Mortgages.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "mortgages",
        rc.log_path / "Log_mortgages.log",
    )

    logger.info("Starting calculation for mortgages.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for mortgages.")
        logger.handlers.clear()


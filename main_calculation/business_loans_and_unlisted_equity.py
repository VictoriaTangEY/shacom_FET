from util.loggers import createLogHandler


def run_business_loans_and_unlisted_equity(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Business loans and unlisted equity.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "business_loans_and_unlisted_equity",
        rc.log_path / "Log_business_loans_and_unlisted_equity.log",
    )

    logger.info("Starting calculation for business loans and unlisted equity.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for business loans and unlisted equity.")
        logger.handlers.clear()


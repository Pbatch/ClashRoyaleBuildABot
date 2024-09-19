import subprocess
from time import sleep

from loguru import logger

from error_handling import WikifiedError


def _is_branch_late() -> bool:
    subprocess.run(
        ["git", "fetch"], check=True, capture_output=True, text=True
    )

    status = subprocess.run(
        ["git", "status", "-uno"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return "Your branch is up to date" not in status


def _check_and_pull_updates() -> None:
    if not _is_branch_late():
        return

    should_update = input(
        "New updates available. Do you want to update the bot? [y]/n: "
    )
    if should_update.lower() not in ["y", "yes", ""]:
        return
    subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)


def check_and_pull_updates() -> None:
    try:
        _check_and_pull_updates()
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr:
            err = "We recommend getting the project using git."
            err += "You won't be able to get any updates until you do."
            logger.warning(err)
            sleep(3)
            return
        logger.error(f"Error while checking / pulling updates: {e.stderr}")
        raise WikifiedError(
            "000", "Error while checking / pulling updates"
        ) from e

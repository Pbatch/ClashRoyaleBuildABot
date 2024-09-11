import subprocess
import sys

from loguru import logger


def _is_branch_late() -> bool:
    # Fetch the latest changes from the remote repository
    subprocess.run(
        ["git", "fetch"], check=True, capture_output=True, text=True
    )

    # Check if the local branch is behind the remote branch
    # Get the local status to check if it's up to date
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
        logger.error(f"Error while checking / pulling updates: {e.stderr}")
        sys.exit(1)

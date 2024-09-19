def get_wikified_error_message(error_code: str, reason: str) -> str:
    return f"Error #E{str(error_code)}: {reason}.\
     See https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/Troubleshooting#error-e{str(error_code)} for more information.\
    Full error message below:\n\n"

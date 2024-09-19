def get_wikified_error_message(error_code: str, reason: str) -> str:
    err_str = f"\u26A0 Error #E{str(error_code)}: {reason}"
    link = "https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/"
    link += f"Troubleshooting#error-e{str(error_code)}"
    err_str += f" See {link} for more information."
    err_str += " You might find more context above this error.\n\n"
    return err_str


class WikifiedError(Exception):
    def __init__(self, error_code: str, reason: str):
        self.error_code = error_code
        self.reason = reason
        super().__init__(get_wikified_error_message(error_code, reason))

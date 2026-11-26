def get_wikified_error_message(error_code: str, reason: str) -> str:
    err_str = f"\u26a0 Error #E{error_code!s}: {reason}"
    link = "https://pbatch.github.io/ClashRoyaleBuildABot/"
    link += f"troubleshooting/#error-e{error_code!s}"
    err_str += f" See {link} for more information."
    err_str += " You might find more context above this error.\n\n"
    return err_str


class WikifiedError(Exception):
    def __init__(self, error_code: str, reason: str) -> None:
        self.error_code = error_code
        self.reason = reason
        super().__init__(get_wikified_error_message(error_code, reason))

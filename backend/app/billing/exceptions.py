class JournalStatusError(Exception):
    def __init__(self, error_msg: str, journal_id: str):
        super().__init__(error_msg)
        self.error_msg = error_msg
        self.journal_id = journal_id


class JournalSubmitError(Exception):
    def __init__(self, error_msg: str, journal_id: str):
        super().__init__(error_msg)
        self.error_msg = error_msg
        self.journal_id = journal_id


class ExchangeRatesClientError(Exception):
    pass

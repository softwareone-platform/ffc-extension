from __future__ import annotations


class InvalidDataSourceIdError(ValueError):
    def __init__(self, datasource_id: str, provider_name: str) -> None:
        self.datasource_id = datasource_id
        self.provider_name = provider_name
        super().__init__(
            f"The format of the datasource id '{datasource_id}' "
            f"does not match the format of the provider '{provider_name}'."
        )

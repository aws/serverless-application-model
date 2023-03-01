import hashlib
from abc import ABC, abstractmethod


class BaseDialup(ABC):
    """BaseDialup class to provide an interface for all dialup classes"""

    def __init__(self, region_config, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.region_config = region_config

    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Returns a bool on whether this dialup is enabled or not
        """

    def __str__(self) -> str:
        return self.__class__.__name__


class DisabledDialup(BaseDialup):
    """
    A dialup that is never enabled
    """

    def __init__(self, region_config, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(region_config)

    def is_enabled(self) -> bool:
        return False


class ToggleDialup(BaseDialup):
    """
    A simple toggle Dialup
    Example of region_config: { "type": "toggle", "enabled": True }
    """

    def __init__(self, region_config, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(region_config)
        self.region_config = region_config

    def is_enabled(self):  # type: ignore[no-untyped-def]
        return self.region_config.get("enabled", False)


class SimpleAccountPercentileDialup(BaseDialup):
    """
    Simple account percentile dialup, enabling X% of
    Example of region_config: { "type": "account-percentile", "enabled-%": 20 }
    """

    def __init__(self, region_config, account_id, feature_name, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(region_config)
        self.account_id = account_id
        self.feature_name = feature_name

    def _get_account_percentile(self) -> int:
        """
        Get account percentile based on sha256 hash of account ID and feature_name

        :returns: integer n, where 0 <= n < 100
        """
        m = hashlib.sha256()
        m.update(self.account_id.encode())
        m.update(self.feature_name.encode())
        return int(m.hexdigest(), 16) % 100

    def is_enabled(self) -> bool:
        """
        Enable when account_percentile falls within target_percentile
        Meaning only (target_percentile)% of accounts will be enabled
        """
        target_percentile: int = self.region_config.get("enabled-%", 0)
        return self._get_account_percentile() < target_percentile

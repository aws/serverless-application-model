import hashlib


class BaseDialup(object):
    """BaseDialup class to provide an interface for all dialup classes"""

    def __init__(self, region_config, **kwargs):
        self.region_config = region_config

    def is_enabled(self):
        """
        Returns a bool on whether this dialup is enabled or not
        """
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__


class DisabledDialup(BaseDialup):
    """
    A dialup that is never enabled
    """

    def __init__(self, region_config, **kwargs):
        super(DisabledDialup, self).__init__(region_config)

    def is_enabled(self):
        return False


class ToggleDialup(BaseDialup):
    """
    A simple toggle Dialup
    Example of region_config: { "type": "toggle", "enabled": True }
    """

    def __init__(self, region_config, **kwargs):
        super(ToggleDialup, self).__init__(region_config)
        self.region_config = region_config

    def is_enabled(self):
        return self.region_config.get("enabled", False)


class SimpleAccountPercentileDialup(BaseDialup):
    """
    Simple account percentile dialup, enabling X% of
    Example of region_config: { "type": "account-percentile", "enabled-%": 20 }
    """

    def __init__(self, region_config, account_id, feature_name, **kwargs):
        super(SimpleAccountPercentileDialup, self).__init__(region_config)
        self.account_id = account_id
        self.feature_name = feature_name

    def _get_account_percentile(self):
        """
        Get account percentile based on sha256 hash of account ID and feature_name

        :returns: integer n, where 0 <= n < 100
        """
        m = hashlib.sha256()
        m.update(self.account_id.encode())
        m.update(self.feature_name.encode())
        return int(m.hexdigest(), 16) % 100

    def is_enabled(self):
        """
        Enable when account_percentile falls within target_percentile
        Meaning only (target_percentile)% of accounts will be enabled
        """
        target_percentile = self.region_config.get("enabled-%", 0)
        return self._get_account_percentile() < target_percentile

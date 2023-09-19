import hashlib
import json
from typing import Any, Optional


class LogicalIdGenerator:
    # NOTE: Changing the length of the hash will change backwards compatibility. This will break the stability contract
    #       given by this class
    HASH_LENGTH = 10

    def __init__(self, prefix: str, data_obj: Optional[Any] = None, data_hash: Optional[str] = None) -> None:
        """
        Generate logical IDs for resources that are stable, deterministic and platform independent

        :param prefix: Prefix for the logicalId
        :param data_obj: Data object to trigger new changes on. If set to None, this is ignored
        :param data_hash: Pre-computed hash, must be a string
        """

        data_str = ""
        if data_obj:
            data_str = self._stringify(data_obj)

        self._prefix = prefix
        self.data_str = data_str
        self.data_hash = data_hash

    def gen(self) -> str:
        """
        Generate stable LogicalIds based on the prefix and given data. This method ensures that the logicalId is
        deterministic and stable based on input prefix & data object. In other words:

            logicalId changes *if and only if* either the `prefix` or `data_obj` changes

        Internally we simply use a SHA1 of the data and append to the prefix to create the logicalId.

        NOTE: LogicalIDs are how CloudFormation identifies a resource. If this ID changes, CFN will delete and
              create a new resource. This can be catastrophic for most resources. So it is important to be *always*
              backwards compatible here.


        :return: LogicalId that can be used to construct resources
        :rtype string
        """

        data_hash = self.get_hash()
        return f"{self._prefix}{data_hash}"

    def get_hash(self, length: int = HASH_LENGTH) -> str:
        """
        Generate and return a hash of data that can be used as suffix of logicalId

        :return: Hash of data if it was present
        :rtype string
        """

        if self.data_hash:
            return self.data_hash[:length]

        data_hash = ""
        if not self.data_str:
            return data_hash

        encoded_data_str = self.data_str.encode("utf-8")
        data_hash = hashlib.sha1(encoded_data_str).hexdigest()  # noqa: S324

        return data_hash[:length]

    def _stringify(self, data: Any) -> str:
        """
        Stable, platform & language-independent stringification of a data with basic Python type.

        We use JSON to dump a string instead of `str()` method in order to be language independent.

        :param data: Data to be stringified. If this is one of JSON native types like string, dict, array etc, it will
                     be properly serialized. Otherwise this method will throw a TypeError for non-JSON serializable
                     objects
        :return: string representation of the dictionary
        :rtype string
        """
        if isinstance(data, str):
            return data

        # Get the most compact dictionary (separators) and sort the keys recursively to get a stable output
        return json.dumps(data, separators=(",", ":"), sort_keys=True)

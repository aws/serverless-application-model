from enum import Enum
from itertools import chain


class Region(Enum):
    US = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
    AP = ["ap-south-1", "ap-northeast-1", "ap-northeast-2", "ap-northeast-3", "ap-southeast-1", "ap-southeast-2"]
    CA = ["ca-central-1"]
    EU = ["eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1"]
    SA = ["sa-east-1"]
    SPARSE_GLOBAL = [
        "us-east-1",
        "eu-west-1",
        "eu-central-1",
        "ap-northeast-1",
        "ap-southeast-2",
        "sa-east-1",
        "ap-southeast-1",
    ]

    @classmethod
    def all_standard(cls) -> list[str]:
        return list(chain.from_iterable(region.value for region in cls))

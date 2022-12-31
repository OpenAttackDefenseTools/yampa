from enum import Enum


class FilterAction(Enum):
    REJECT = "reject"
    ALERT = "alert"
    ACCEPT = "accept"

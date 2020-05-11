import typing
from functools import total_ordering


@total_ordering
class MinMaxCounter:
    def __init__(self, initial: int, min_value: int, max_value: int):
        self.initial = initial
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial

    def reset(self, v: typing.Optional[int] = None):
        self._set_value(v if v is not None else self.initial)

    def increase(self, v: int):
        self._set_value(self.value + v)

    def decrease(self, v: int):
        self._set_value(self.value - v)

    def _set_value(self, new_value: int):
        self.value = min(max(new_value, self.min_value), self.max_value)

    def __repr__(self):
        return (
            f"{self.__class__.name__}({self.value}, "
            f"min_value={self.min_value}, max_value={self.max_value})"
        )

    def __int__(self):
        return self.value

    def __lt__(self, other: int):
        if isinstance(other, (int, float)):
            return self.value < other
        return NotImplemented

    def __eq__(self, other: int):
        if isinstance(other, (int, float)):
            return self.value == other
        return NotImplemented


class PlayerState:
    def __init__(self):
        self.soap_meter_counter: MinMaxCounter = MinMaxCounter(50000, 0, 50000)
        self.liquid_soap_powerup_counter: MinMaxCounter = MinMaxCounter(0, 0, 3)
        self.antivirus_powerup_counter: MinMaxCounter = MinMaxCounter(0, 0, 3)
        self.score: int = 0
        self.people_counter: MinMaxCounter = MinMaxCounter(300, 0, 10000)

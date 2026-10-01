from dataclasses import dataclass


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def translated(self, dx: float, dy: float) -> Bounds:
        return Bounds(self.min_x + dx, self.min_y + dy, self.max_x + dx, self.max_y + dy)

    def union(self, other: Bounds) -> Bounds:
        return Bounds(
            min(self.min_x, other.min_x),
            min(self.min_y, other.min_y),
            max(self.max_x, other.max_x),
            max(self.max_y, other.max_y),
        )

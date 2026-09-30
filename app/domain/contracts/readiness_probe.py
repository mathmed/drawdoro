from abc import ABC, abstractmethod


class ReadinessProbe(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def is_ready(self) -> bool: ...

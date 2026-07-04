from abc import ABC, abstractmethod
from typing import Any


class PhotoSaverRepository(ABC):

    @abstractmethod
    def save_within_folder(self, file: Any, folder_album_id) -> str:
        pass

    @abstractmethod
    def save(self, file: Any) -> str:
        pass

    @abstractmethod
    def delete(self, file_url: str) -> bool:
        pass

    @abstractmethod
    def copy_file(self, source_url: str, target_album_id) -> str:
        pass

    @abstractmethod
    def fetch(self, file_url: str) -> tuple[bytes, str]:
        pass

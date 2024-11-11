import pytest
from icecream import ic

from fastapi_utils.dependency import authorize


class TestGetDecryptionKey:
    def test_get_decryption_key(self):
        key = authorize.get_decryption_key()
        ic(key)

class TestDownloadDecryptionKey:
    def test_download_decryption_key(self):
        key = authorize.download_decryption_key()
        ic(key)

from icecream import ic

import utils
from fastapi_utils.dependencies import authorize


config = utils.get_config()


class TestGetDecryptionKey:
    def test_get_decryption_key(self):
        key = authorize.get_decryption_key()
        ic(key)


class TestDownloadDecryptionKey:
    def test_download_decryption_key(self):
        key = authorize.download_decryption_key()
        ic(key)
        assert (
            key
            == open(
                config["application"]["encryption"]["jwt"]["public_key"], "rb"
            ).read()
        )

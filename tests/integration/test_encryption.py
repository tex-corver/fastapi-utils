from icecream import ic  # type: ignore

from fastapi_utils.dependency import authorize  # type: ignore


class TestGetDecryptionKey:
    def test_get_decryption_key(self) -> None:
        key = authorize.get_decryption_key()
        ic(key)


# class TestDownloadDecryptionKey:
#     def test_download_decryption_key(self):
#         key = authorize.download_decryption_key()
#         ic(key)

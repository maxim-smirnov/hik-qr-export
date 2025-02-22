import base64
import pyaes

class HikAES(pyaes.AES):
    def __init__(self, key: bytes = b'dkfj4593@#&*wlfm', rounds: int = 4):
        self.number_of_rounds = {16: rounds, 24: rounds, 32: rounds}
        super().__init__(key)

    def decrypt_b64_to_str(self, ciphertext: str) -> str:
        return ''.join(chr(c) for c in self.decrypt(base64.b64decode(ciphertext)))

    def encrypt_str_to_b64(self, plaintext: str) -> str:
        return base64.b64encode(bytearray(self.encrypt(plaintext.encode()))).decode()

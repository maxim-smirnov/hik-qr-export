import base64
import pyaes

class HikAES(pyaes.AES):
    def __init__(self, key: bytes = b'dkfj4593@#&*wlfm', rounds: int = 4):
        self.number_of_rounds = {16: rounds, 24: rounds, 32: rounds}
        super().__init__(key)

    def decrypt_b64_to_str(self, ciphertext: str) -> str:
        raw = base64.b64decode(ciphertext)
        plaintext = []
        for i in range(0, len(raw), 16):
            plaintext.extend(self.decrypt(list(raw[i:i + 16])))
        return ''.join(chr(c) for c in plaintext)

    def encrypt_str_to_b64(self, plaintext: str) -> str:
        raw = plaintext.encode()
        ciphertext = []
        for i in range(0, len(raw), 16):
            ciphertext.extend(self.encrypt(list(raw[i:i + 16])))
        return base64.b64encode(bytearray(ciphertext)).decode()

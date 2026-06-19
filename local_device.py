import base64

from errors import InvalidLengthError, MalformedDeviceDataError
from hik_aes import HikAES

class LocalDevice:
    _name: str
    _ip_address: str
    _port: int
    _username: str
    _password: str

    _BLOCK_SIZE: int = 16
    _MAX_BLOCKS: int = 2

    def __init__(self, name: str, ip_address: str, port: int, username: str, password: str):
        max_len = self._BLOCK_SIZE * self._MAX_BLOCKS
        if len(username) > max_len:
            raise InvalidLengthError(f'username length must be not more than {max_len} characters')
        if len(password) > max_len:
            raise InvalidLengthError(f'password length must be not more than {max_len} characters')
        self._name = name
        self._ip_address = ip_address
        self._port = port
        self._username = username
        self._password = password

    @classmethod
    def from_encoded(cls, ampersand_string: str) -> 'LocalDevice':
        try:
            name_b64, _, ip_address_b64, port, _, username_enc_b64, password_enc_b64 = ampersand_string.split('&')
        except ValueError:
            raise MalformedDeviceDataError(
                f'not enough fields in ampersand string (expected 7, got {ampersand_string.count("&")})'
            )
        username = HikAES().decrypt_b64_to_str(username_enc_b64).rstrip('\x00')
        password = HikAES().decrypt_b64_to_str(password_enc_b64).rstrip('\x00')
        return cls(
            name=base64.b64decode(name_b64).decode('utf-8'),
            ip_address=base64.b64decode(ip_address_b64).decode('utf-8'),
            port=int(port),
            username=username,
            password=password
        )

    @staticmethod
    def _pad_to_block(value: str, block_size: int = 16) -> str:
        """Pad string to the next multiple of block_size using null bytes."""
        padded_len = ((len(value) + block_size - 1) // block_size) * block_size
        return value.ljust(padded_len, '\x00')

    def encode(self) -> str:
        username_padded = self._pad_to_block(self._username)
        password_padded = self._pad_to_block(self._password)
        return '&'.join([
            base64.b64encode(self._name.encode('utf-8')).decode(),
            '0',  # Always 0 in my cases (maybe device type)
            base64.b64encode(self._ip_address.encode('utf-8')).decode(),
            str(self._port),
            '',  # Always empty in my cases
            HikAES().encrypt_str_to_b64(username_padded),
            HikAES().encrypt_str_to_b64(password_padded),
        ])

    @property
    def name(self) -> str:
        return self._name

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def port(self) -> int:
        return self._port

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    def __repr__(self):
        return (f'{self.__class__.__name__}(name=\'{self.name}\', ip_address=\'{self.ip_address}\', port={self.port}, '
                f'username=\'{self.username}\', password=\'{self.password}\')')

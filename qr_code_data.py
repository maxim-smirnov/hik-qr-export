import base64
import datetime
import zlib

from errors import InvalidLengthError, MalformedQRStringError
from hik_aes import HikAES
from local_device import LocalDevice


class QrCodeData:
    _e2e_password: str
    _timestamp_created: int|None
    _local_devices: [LocalDevice]

    def __init__(
            self,
            e2e_password: str,
            local_devices: [LocalDevice],
            header: str = 'QRC03010003',
            timestamp_created: int = int(datetime.datetime.now().timestamp())
    ):
        if len(e2e_password) > 16:
            raise InvalidLengthError('e2e_password length must be not more than 16 characters')
        self._e2e_password = e2e_password
        self._local_devices = local_devices
        self._header = header
        self._timestamp_created = timestamp_created

    @classmethod
    def from_qr_string(cls, qr_string: str) -> 'QrCodeData':
        header = qr_string[:11]
        compressed_data_b64 = qr_string[11:]

        decompressed_data = zlib.decompress(base64.b64decode(compressed_data_b64)).decode()

        decompressed_data_list = decompressed_data.split(':')

        if len(decompressed_data_list) == 2:
            e2e_password_enc_b64, local_devices_str = decompressed_data_list
            timestamp_created = None
        elif len(decompressed_data_list) == 3:
            e2e_password_enc_b64, local_devices_str, timestamp_created_enc = decompressed_data_list
            timestamp_created = int(HikAES().decrypt_b64_to_str(timestamp_created_enc).rstrip('\x00'))
        else:
            raise MalformedQRStringError

        e2e_password = HikAES().decrypt_b64_to_str(e2e_password_enc_b64).rstrip('\x00')

        local_devices = []
        for local_device_encoded in local_devices_str.split('$'):
            if not len(local_device_encoded):
                continue
            local_devices.append(
                LocalDevice.from_encoded(local_device_encoded)
            )

        return cls(
            e2e_password=e2e_password,
            local_devices=local_devices,
            header=header,
            timestamp_created=timestamp_created
        )

    def renew(self):
        self._timestamp_created = int(datetime.datetime.now().timestamp())

    def encode(self) -> str:
        local_devices_str = '$'.join(local_device.encode() for local_device in self._local_devices) + '$'

        data_to_merge_list = [
            HikAES().encrypt_str_to_b64(self._e2e_password.ljust(16, '\x00')),
            local_devices_str
        ]

        if self._timestamp_created:
            data_to_merge_list.append(
                HikAES().encrypt_str_to_b64(str(self._timestamp_created).ljust(16, '\x00'))
            )

        compressed_data_b64 = base64.b64encode(zlib.compress(':'.join(data_to_merge_list).encode())).decode()
        return f'{self._header}{compressed_data_b64}'

    @property
    def e2e_password(self) -> str:
        return self._e2e_password

    @property
    def local_devices(self) -> [LocalDevice]:
        return self._local_devices

    @property
    def header(self) -> str:
        return self._header

    @property
    def timestamp_created(self) -> int|None:
        return self._timestamp_created

    @timestamp_created.setter
    def timestamp_created(self, value: int):
        self._timestamp_created = value

    def __repr__(self):
        return (f'{self.__class__.__name__}(header=\'{self.header}\', e2e_password=\'{self._e2e_password}\', '
                f'timestamp_created={self.timestamp_created})')

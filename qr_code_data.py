import base64
import datetime
import zlib

from errors import InvalidLengthError, MalformedQRStringError
from hik_aes import HikAES
from local_device import LocalDevice


class QrCodeData:
    _e2e_password: str|None
    _timestamp_created: int|None
    _local_devices: [LocalDevice]
    _device_separator: str

    _SEPARATORS: dict[str, str] = {'$': '&', ';': ','}
    _DEFAULT_DEVICE_SEPARATOR: str = '$'

    _HEADER_LENGTHS: dict[str, int] = {'iVMS': 12, 'DVR/NVR': 13}
    _DEFAULT_HEADER_LENGTH: int = 11

    def __init__(
            self,
            e2e_password: str|None,
            local_devices: [LocalDevice],
            header: str = 'QRC03010002',
            timestamp_created: int = int(datetime.datetime.now().timestamp()),
            device_separator: str = _DEFAULT_DEVICE_SEPARATOR
    ):
        if e2e_password is not None and len(e2e_password) > 16:
            raise InvalidLengthError('e2e_password length must be not more than 16 characters')
        if device_separator not in self._SEPARATORS:
            raise MalformedQRStringError(
                f'unknown device separator \'{device_separator}\' '
                f'(expected one of {", ".join(self._SEPARATORS)})'
            )
        self._device_separator = device_separator
        self._e2e_password = e2e_password
        self._local_devices = local_devices
        self._header = header
        self._timestamp_created = timestamp_created

    @classmethod
    def from_qr_string(cls, qr_string: str) -> 'QrCodeData':
        header_length = cls._detect_header_length(qr_string)

        header = qr_string[:header_length]
        compressed_data_b64 = qr_string[header_length:]
        decompressed_data = zlib.decompress(base64.b64decode(compressed_data_b64)).decode()
        decompressed_data_list = decompressed_data.split(':')

        if len(decompressed_data_list) == 1:
            local_devices_str = decompressed_data_list[0]

            timestamp_created = None
            e2e_password = None
        elif len(decompressed_data_list) == 2:
            e2e_password_enc_b64, local_devices_str = decompressed_data_list

            timestamp_created = None
            e2e_password = HikAES().decrypt_b64_to_str(e2e_password_enc_b64).rstrip('\x00')
        elif len(decompressed_data_list) == 3:
            e2e_password_enc_b64, local_devices_str, timestamp_created_enc = decompressed_data_list

            timestamp_created = int(HikAES().decrypt_b64_to_str(timestamp_created_enc).rstrip('\x00'))
            e2e_password = HikAES().decrypt_b64_to_str(e2e_password_enc_b64).rstrip('\x00')
        else:
            raise MalformedQRStringError

        device_separator = cls._detect_device_separator(local_devices_str)

        local_devices = []
        for local_device_encoded in local_devices_str.split(device_separator):
            if not len(local_device_encoded):
                continue
            local_devices.append(
                LocalDevice.from_encoded(local_device_encoded, cls._SEPARATORS[device_separator])
            )

        return cls(
            e2e_password=e2e_password,
            local_devices=local_devices,
            header=header,
            timestamp_created=timestamp_created,
            device_separator=device_separator
        )

    @classmethod
    def _detect_header_length(cls, qr_string: str) -> int:
        """Detect the header length of the QR string by its known prefixes."""
        for header_prefix, header_length in cls._HEADER_LENGTHS.items():
            if qr_string.startswith(header_prefix):
                return header_length
        return cls._DEFAULT_HEADER_LENGTH

    @classmethod
    def _detect_device_separator(cls, local_devices_str: str) -> str:
        """Detect which separator flavour is used by the encoded devices part."""
        for device_separator, field_separator in cls._SEPARATORS.items():
            if device_separator in local_devices_str or field_separator in local_devices_str:
                return device_separator
        return cls._DEFAULT_DEVICE_SEPARATOR

    def renew(self):
        self._timestamp_created = int(datetime.datetime.now().timestamp())

    def encode(self) -> str:
        if self._e2e_password is None and self._timestamp_created:
            raise MalformedQRStringError(
                'QR code has no password part, so there is no place for the timestamp part'
            )

        field_separator = self._SEPARATORS[self._device_separator]
        local_devices_str = self._device_separator.join(
            local_device.encode(field_separator) for local_device in self._local_devices
        ) + self._device_separator

        data_to_merge_list = []

        if self._e2e_password is not None:
            data_to_merge_list.append(
                HikAES().encrypt_str_to_b64(self._e2e_password.ljust(16, '\x00'))
            )

        data_to_merge_list.append(local_devices_str)

        if self._timestamp_created:
            data_to_merge_list.append(
                HikAES().encrypt_str_to_b64(str(self._timestamp_created).ljust(16, '\x00'))
            )

        compressed_data_b64 = base64.b64encode(zlib.compress(':'.join(data_to_merge_list).encode())).decode()
        return f'{self._header}{compressed_data_b64}'

    @property
    def e2e_password(self) -> str|None:
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

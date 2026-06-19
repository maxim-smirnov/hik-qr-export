import click
import datetime
from qr_code_data import QrCodeData


def _read_qr_from_clipboard() -> str:
    """Read a QR code from the macOS clipboard image and return its text content.

    Uses PIL.ImageGrab to capture the clipboard image and zxingcpp to decode
    any QR codes found within.

    Returns:
        The text content of the single QR code found in the clipboard image.

    Raises:
        click.ClickException: If no image is in the clipboard, no QR code is
            detected, or multiple QR codes are found.
    """
    import PIL.ImageGrab
    import zxingcpp

    image = PIL.ImageGrab.grabclipboard()
    if image is None:
        raise click.ClickException('No image found in clipboard.')

    results = zxingcpp.read_barcodes(image)
    qr_codes = [r for r in results if r.format == zxingcpp.BarcodeFormat.QRCode]

    if not qr_codes:
        raise click.ClickException('No QR code detected in the clipboard image.')
    if len(qr_codes) > 1:
        raise click.ClickException(f'Multiple QR codes detected ({len(qr_codes)}); expected exactly one.')

    return qr_codes[0].text


@click.group()
def cli():
    pass

@cli.command(help='Decode QR code data, extract metadata and stored devices.')
@click.argument('qr_string', required=False, default=None)
@click.option('-c', '--clipboard', is_flag=True, default=False, help='Read QR code image from macOS clipboard.')
def decode(qr_string: str | None, clipboard: bool) -> None:
    if clipboard:
        qr_string = _read_qr_from_clipboard()
    elif qr_string is None:
        raise click.UsageError('Provide a QR string argument or use -c/--clipboard.')

    qr_code_data = QrCodeData.from_qr_string(qr_string)
    click.echo(f'Data header: {qr_code_data.header}')
    if qr_code_data.e2e_password:
        click.echo(f'Password used: {qr_code_data.e2e_password}')
    else:
        click.echo('QR code has no password part!', err=True)
    if qr_code_data.timestamp_created:
        click.echo(f'QR code generated at: {qr_code_data.timestamp_created} '
                   f'({datetime.datetime.fromtimestamp(qr_code_data.timestamp_created).isoformat()})')
    else:
        click.echo(f'QR code has no timestamp part!', err=True)
    for local_device in qr_code_data.local_devices:
        click.echo()
        click.echo(f'Device Name: {local_device.name}')
        click.echo(f'IP Address: {local_device.ip_address}')
        click.echo(f'Port: {local_device.port}')
        click.echo(f'Username: {local_device.username}')
        click.echo(f'Password: {local_device.password}')

@cli.command(help='Renew QR code.')
@click.argument('qr_string')
@click.option('-q', '--quiet', default=False, is_flag=True, help='Suppress printing timestamps.')
@click.option('--timestamp', default=None, type=click.INT, help='Specify exact timestamp to use.')
def renew(qr_string, quiet, timestamp):
    qr_code_data = QrCodeData.from_qr_string(qr_string)
    if not quiet:
        if qr_code_data.timestamp_created:
            click.echo(f'QR code generated at: {qr_code_data.timestamp_created} '
                       f'({datetime.datetime.fromtimestamp(qr_code_data.timestamp_created).isoformat()})')
        else:
            click.echo(f'QR code has no timestamp part!', err=True)
    if timestamp is None:
        qr_code_data.renew()
    else:
        qr_code_data.timestamp_created = timestamp
    if not quiet:
        click.echo(f'New timestamp of QR creation is: {qr_code_data.timestamp_created} '
                   f'({datetime.datetime.fromtimestamp(qr_code_data.timestamp_created).isoformat()})')
    click.echo(qr_code_data.encode())


if __name__ == '__main__':
    cli()
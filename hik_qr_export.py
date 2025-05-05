import click
import datetime
from qr_code_data import QrCodeData


@click.group()
def cli():
    pass

@cli.command(help='Decode QR code data, extract metadata and stored devices.')
@click.argument('qr_string')
def decode(qr_string):
    qr_code_data = QrCodeData.from_qr_string(qr_string)
    click.echo(f'Data header: {qr_code_data.header}')
    click.echo(f'Password used: {qr_code_data.e2e_password}')
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
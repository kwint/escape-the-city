import qrcode
from io import BytesIO
from django.http import HttpResponse


def generate_qr_code(data, size=10):
    """
    Generates a QR code image for the given data.

    Args:
        data: The data to encode in the QR code (typically a URL)
        size: The size of the QR code (default: 10)

    Returns:
        HttpResponse with the PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = 'inline; filename="qr_code.png"'

    return response

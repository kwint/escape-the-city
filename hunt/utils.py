from pathlib import Path

import qrcode
from io import BytesIO
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def generate_qr_code(data: str, size: int = 10) -> HttpResponse:
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


def _make_qr_image(data: str) -> ImageReader:
    """Generate a QR code as a reportlab-compatible ImageReader."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


LOGO_PATH = Path(__file__).resolve().parent / "static" / "hunt" / "logo.png"


def generate_posts_pdf(posts: list, base_url: str) -> HttpResponse:
    """
    Generate a single PDF with one page per post, each containing:
    - Optional logo (from hunt/static/hunt/logo.png)
    - Post name
    - QR code linking to the scan page

    Args:
        posts: Queryset or list of Post objects.
        base_url: The scheme + host (e.g. "https://example.com") for building scan URLs.

    Returns:
        HttpResponse with the PDF file.
    """
    buf = BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    has_logo = LOGO_PATH.is_file()

    for post in posts:
        scan_url = f"{base_url}/scan/{post.qr_code_identifier}/"
        qr_img = _make_qr_image(scan_url)

        # -- optional logo centred at top --
        y_cursor = page_h - 30 * mm
        if has_logo:
            logo = ImageReader(str(LOGO_PATH))
            logo_w_native, logo_h_native = logo.getSize()
            max_logo_h = 30 * mm
            scale = max_logo_h / logo_h_native
            logo_w = logo_w_native * scale
            logo_h = max_logo_h
            c.drawImage(
                logo,
                (page_w - logo_w) / 2,
                y_cursor - logo_h,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
            y_cursor -= logo_h + 10 * mm

        # -- post name --
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(page_w / 2, y_cursor - 36, post.name)
        y_cursor -= 36 + 20 * mm

        # -- QR code --
        qr_size = 120 * mm
        c.drawImage(
            qr_img,
            (page_w - qr_size) / 2,
            y_cursor - qr_size,
            width=qr_size,
            height=qr_size,
        )

        c.showPage()

    c.save()
    buf.seek(0)

    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="posten_qr_codes.pdf"'
    return response

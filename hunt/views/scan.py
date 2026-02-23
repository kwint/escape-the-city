from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse
from django.contrib import messages
from django.utils import timezone

from ..models import Post, Group, Scan


def scan_post(request, qr_code_identifier):
    """
    View for when a QR code is scanned.
    Shows a form to enter group password.
    """
    post = get_object_or_404(Post, qr_code_identifier=qr_code_identifier)

    if request.method == 'POST':
        group_password = request.POST.get('password', '').strip()

        if not group_password:
            messages.error(request, 'Voer je groepswachtwoord in.')
            return render(request, 'hunt/scan.html', {'post': post})

        try:
            group = Group.objects.get(password=group_password)

            # Check if this group has already scanned this post
            if not Scan.objects.filter(group=group, post=post).exists():
                # Create a new scan record
                Scan.objects.create(group=group, post=post, scanned_at=timezone.now())

            # Redirect to download/success page
            return redirect('scan_success', qr_code_identifier=qr_code_identifier, group_id=group.id)

        except Group.DoesNotExist:
            messages.error(request, 'Ongeldig groepswachtwoord. Probeer opnieuw.')
            return render(request, 'hunt/scan.html', {'post': post})

    return render(request, 'hunt/scan.html', {'post': post})


def scan_success(request, qr_code_identifier, group_id):
    """
    View shown after successful scan.
    Shows success message and download button if PDF is available.
    """
    post = get_object_or_404(Post, qr_code_identifier=qr_code_identifier)
    group = get_object_or_404(Group, id=group_id)

    # Verify that this group has scanned this post
    scan = Scan.objects.filter(group=group, post=post).first()

    if not scan:
        messages.error(request, 'Toegang geweigerd. Scan eerst de QR code en voer je wachtwoord in.')
        return redirect('scan_post', qr_code_identifier=qr_code_identifier)

    context = {
        'post': post,
        'group': group,
        'has_pdf': bool(post.pdf_file),
    }

    return render(request, 'hunt/scan_success.html', context)


def download_pdf(request, qr_code_identifier, group_id):
    """
    View to download the PDF instructions after successful authentication.
    """
    post = get_object_or_404(Post, qr_code_identifier=qr_code_identifier)
    group = get_object_or_404(Group, id=group_id)

    # Verify that this group has scanned this post
    scan = Scan.objects.filter(group=group, post=post).first()

    if not scan:
        messages.error(request, 'Toegang geweigerd. Scan eerst de QR code en voer je wachtwoord in.')
        return redirect('scan_post', qr_code_identifier=qr_code_identifier)

    # Check if PDF exists
    if not post.pdf_file:
        messages.error(request, 'Geen PDF beschikbaar voor deze post.')
        return redirect('scan_success', qr_code_identifier=qr_code_identifier, group_id=group_id)

    # Serve the PDF file
    try:
        return FileResponse(post.pdf_file.open('rb'), content_type='application/pdf', as_attachment=True, filename=f'{post.name}_instructies.pdf')
    except Exception as e:
        messages.error(request, 'Fout bij downloaden van PDF bestand.')
        return redirect('scan_success', qr_code_identifier=qr_code_identifier, group_id=group_id)

from django.shortcuts import get_object_or_404, redirect

from ..models import Post, Group
from ..utils import generate_qr_code


def generate_qr(request, post_id):
    """
    View to generate and display a QR code for a specific post.
    Only accessible to admin users.
    """
    if not request.user.is_staff:
        return redirect('/admin/login/')

    post = get_object_or_404(Post, id=post_id)
    qr_url = post.get_qr_url(request)

    return generate_qr_code(qr_url)


def generate_group_qr(request, group_id):
    """
    View to generate and display a QR code for a group (for tagging).
    Only accessible to admin users.
    """
    if not request.user.is_staff:
        return redirect('/admin/login/')

    group = get_object_or_404(Group, id=group_id)
    qr_url = group.get_tag_url(request)

    return generate_qr_code(qr_url)

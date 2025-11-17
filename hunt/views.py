from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.contrib import messages
from django.utils import timezone
from .models import Post, Group, Scan
from .utils import generate_qr_code


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
            existing_scan = Scan.objects.filter(group=group, post=post).first()

            if existing_scan:
                messages.info(request, f'Je groep heeft deze post al gescand op {existing_scan.scanned_at.strftime("%Y-%m-%d %H:%M:%S")}.')
            else:
                # Create a new scan record
                Scan.objects.create(group=group, post=post, scanned_at=timezone.now())
                messages.success(request, f'Scan succesvol geregistreerd voor {group}!')

            # Redirect to download page
            return redirect('download_pdf', qr_code_identifier=qr_code_identifier, group_id=group.id)

        except Group.DoesNotExist:
            messages.error(request, 'Ongeldig groepswachtwoord. Probeer opnieuw.')
            return render(request, 'hunt/scan.html', {'post': post})

    return render(request, 'hunt/scan.html', {'post': post})


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

    # Serve the PDF file
    try:
        return FileResponse(post.pdf_file.open('rb'), content_type='application/pdf', as_attachment=True, filename=f'{post.name}_instructies.pdf')
    except Exception as e:
        messages.error(request, 'Fout bij downloaden van PDF bestand.')
        return redirect('scan_post', qr_code_identifier=qr_code_identifier)


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


def overview(request):
    """
    Overview page showing a matrix of all posts and groups with scan status.
    """

    # Get all groups and posts ordered
    groups = Group.objects.all().order_by('scout_group', 'name')
    posts = Post.objects.all().order_by('order', 'name')
    num_groups = len(groups)

    # Get all scans and create a lookup dict
    scans = Scan.objects.all().select_related('group', 'post')
    scan_lookup = {(scan.group_id, scan.post_id): scan for scan in scans}

    # Calculate points for each post based on scan order
    post_points = {}  # {post_id: {group_id: points}}
    for post in posts:
        # Get all scans for this post ordered by time
        post_scans = sorted(
            [s for s in scans if s.post_id == post.id],
            key=lambda s: s.scanned_at
        )
        post_points[post.id] = {}
        for idx, scan in enumerate(post_scans):
            # First gets N points, second gets N-1, etc.
            points = num_groups - idx
            if points > 0:
                post_points[post.id][scan.group_id] = points

    # Create matrix data structure with groups as rows
    matrix = []
    for group in groups:
        row = {
            'group': group,
            'scans': [],
            'total_completed': 0,
            'total_points': 0
        }
        for post in posts:
            scan = scan_lookup.get((group.id, post.id))
            points = post_points.get(post.id, {}).get(group.id, 0)
            completed = scan is not None
            row['scans'].append({
                'post': post,
                'scan': scan,
                'completed': completed,
                'points': points
            })
            if completed:
                row['total_completed'] += 1
            row['total_points'] += points
        matrix.append(row)

    # Calculate post totals (how many groups completed each post)
    post_totals = []
    for post in posts:
        total = sum(1 for scan in scans if scan.post_id == post.id)
        post_totals.append(total)

    # Calculate statistics
    total_possible_scans = len(groups) * len(posts)
    total_scans = len(scans)
    remaining_scans = total_possible_scans - total_scans

    # Find farthest post scanned (highest order number with at least one scan)
    farthest_post = None
    scanned_post_ids = set(scan.post_id for scan in scans)
    for post in reversed(posts):  # Start from highest order
        if post.id in scanned_post_ids:
            farthest_post = post
            break

    # Find first place group (highest points)
    first_place_group = None
    first_place_points = 0
    for row in matrix:
        if row['total_points'] > first_place_points:
            first_place_points = row['total_points']
            first_place_group = row['group']

    context = {
        'groups': groups,
        'posts': posts,
        'matrix': matrix,
        'post_totals': post_totals,
        'remaining_scans': remaining_scans,
        'farthest_post': farthest_post,
        'first_place_group': first_place_group,
        'first_place_points': first_place_points,
    }

    return render(request, 'hunt/overview.html', context)

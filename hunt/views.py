from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Post, Group, Scan, Tag, GameSettings
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
            if not Scan.objects.filter(group=group, post=post).exists():
                # Create a new scan record
                Scan.objects.create(group=group, post=post, scanned_at=timezone.now())

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


def tag_group(request):
    """
    View for taggers to tag a group.
    Requires group password and tagger name.
    Each tag subtracts 1 point from the group's score.
    """
    if request.method == 'POST':
        group_password = request.POST.get('password', '').strip()
        tagger_name = request.POST.get('tagger_name', '').strip()

        # Validate inputs
        if not group_password:
            messages.error(request, 'Voer het groepswachtwoord in.')
            return render(request, 'hunt/tag.html')

        if not tagger_name:
            messages.error(request, 'Voer je naam in.')
            return render(request, 'hunt/tag.html')

        try:
            group = Group.objects.get(password=group_password)

            # Check cooldown period (5 minutes)
            cooldown_time = timezone.now() - timedelta(minutes=5)
            last_tag = Tag.objects.filter(group=group).order_by('-tagged_at').first()

            if last_tag and last_tag.tagged_at > cooldown_time:
                time_remaining = 5 - int((timezone.now() - last_tag.tagged_at).total_seconds() / 60)
                messages.error(request, f'Deze groep is recent getagd. Probeer het over {time_remaining} minuten opnieuw.')
                return render(request, 'hunt/tag.html')

            # Create tag record
            Tag.objects.create(group=group, tagger_name=tagger_name, tagged_at=timezone.now())

            # Get current tag count for this group
            tag_count = Tag.objects.filter(group=group).count()

            messages.success(request, f'Groep "{group}" succesvol getagd! ({tag_count} tags totaal)')
            return render(request, 'hunt/tag.html')

        except Group.DoesNotExist:
            messages.error(request, 'Ongeldig groepswachtwoord. Probeer opnieuw.')
            return render(request, 'hunt/tag.html')

    return render(request, 'hunt/tag.html')


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

    # Get all tags and count them per group
    tags = Tag.objects.all().select_related('group')
    tag_counts = {}  # {group_id: count}
    last_tags = {}   # {group_id: last_tag_object}
    for tag in tags:
        tag_counts[tag.group_id] = tag_counts.get(tag.group_id, 0) + 1
        if tag.group_id not in last_tags or tag.tagged_at > last_tags[tag.group_id].tagged_at:
            last_tags[tag.group_id] = tag

    # Load game settings dynamically
    settings = GameSettings.load()
    POINTS_PER_SCAN = settings.points_per_scan
    STARTING_POINTS = settings.starting_points
    TAG_PENALTY = settings.tag_penalty

    # Create matrix data structure with groups as rows
    matrix = []
    for group in groups:
        row = {
            'group': group,
            'scans': [],
            'total_completed': 0,
            'total_points': STARTING_POINTS,  # Start with configured starting points
            'tag_count': tag_counts.get(group.id, 0),
            'last_tag': last_tags.get(group.id),
        }
        for post in posts:
            scan = scan_lookup.get((group.id, post.id))
            completed = scan is not None
            points = POINTS_PER_SCAN if completed else 0
            row['scans'].append({
                'post': post,
                'scan': scan,
                'completed': completed,
                'points': points
            })
            if completed:
                row['total_completed'] += 1
                row['total_points'] += points  # Add configured points for each scan

        # Calculate net score (starting + scan points - tag penalty, minimum 0)
        row['tag_penalty'] = row['tag_count'] * TAG_PENALTY
        row['net_score'] = max(0, row['total_points'] - row['tag_penalty'])

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

    # Find first place group (highest net score)
    first_place_group = None
    first_place_points = 0
    for row in matrix:
        if row['net_score'] > first_place_points:
            first_place_points = row['net_score']
            first_place_group = row['group']

    # Calculate total tags
    total_tags = len(tags)

    context = {
        'groups': groups,
        'posts': posts,
        'matrix': matrix,
        'post_totals': post_totals,
        'remaining_scans': remaining_scans,
        'farthest_post': farthest_post,
        'first_place_group': first_place_group,
        'first_place_points': first_place_points,
        'total_tags': total_tags,
        'settings': settings,  # Pass settings to template for dynamic legend
    }

    return render(request, 'hunt/overview.html', context)

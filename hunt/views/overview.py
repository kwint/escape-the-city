from django.shortcuts import render

from ..models import Post, Group, Scan, Tag, GameSettings


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

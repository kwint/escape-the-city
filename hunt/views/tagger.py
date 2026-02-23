from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta

from ..models import Group, Tagger, Tag


def tagger_login(request):
    """
    Login page for taggers. Password-only login.
    """
    # If already logged in, redirect to dashboard
    if request.session.get('tagger_id'):
        return redirect('tagger_dashboard')

    if request.method == 'POST':
        password = request.POST.get('password', '').strip().lower()

        if not password:
            messages.error(request, 'Voer je wachtwoord in.')
            return render(request, 'hunt/tagger_login.html')

        try:
            tagger = Tagger.objects.get(password=password)
            request.session['tagger_id'] = tagger.id
            messages.success(request, f'Welkom, {tagger.name}!')
            return redirect('tagger_dashboard')
        except Tagger.DoesNotExist:
            messages.error(request, 'Ongeldig wachtwoord.')
            return render(request, 'hunt/tagger_login.html')

    return render(request, 'hunt/tagger_login.html')


def tagger_logout(request):
    """
    Logout the current tagger.
    """
    if 'tagger_id' in request.session:
        del request.session['tagger_id']
    messages.info(request, 'Je bent uitgelogd.')
    return redirect('tagger_login')


def get_current_tagger(request):
    """Helper to get the currently logged in tagger."""
    tagger_id = request.session.get('tagger_id')
    if tagger_id:
        try:
            return Tagger.objects.get(id=tagger_id)
        except Tagger.DoesNotExist:
            del request.session['tagger_id']
    return None


def tag_group(request, qr_code_identifier):
    """
    View for tagging a group via QR code scan.
    Shows group details always. Allows tagging only if logged in.
    """
    group = get_object_or_404(Group, qr_code_identifier=qr_code_identifier)
    tagger = get_current_tagger(request)

    # Get tag statistics for this group
    tag_count = Tag.objects.filter(group=group).count()
    last_tag = Tag.objects.filter(group=group).order_by('-tagged_at').first()

    # Check cooldown
    can_tag = True
    cooldown_remaining = 0
    if last_tag:
        cooldown_time = timezone.now() - timedelta(minutes=5)
        if last_tag.tagged_at > cooldown_time:
            can_tag = False
            cooldown_remaining = 5 - int((timezone.now() - last_tag.tagged_at).total_seconds() / 60)

    context = {
        'group': group,
        'tagger': tagger,
        'tag_count': tag_count,
        'last_tag': last_tag,
        'can_tag': can_tag,
        'cooldown_remaining': cooldown_remaining,
    }

    if request.method == 'POST' and tagger:
        if not can_tag:
            messages.error(request, f'Deze groep is recent getagd. Probeer het over {cooldown_remaining} minuten opnieuw.')
        else:
            # Create tag record
            Tag.objects.create(group=group, tagger=tagger, tagged_at=timezone.now())
            tag_count = Tag.objects.filter(group=group).count()
            messages.success(request, f'Groep "{group}" succesvol getagd! ({tag_count} tags totaal)')

            # Update context after tagging
            context['tag_count'] = tag_count
            context['can_tag'] = False
            context['cooldown_remaining'] = 5

    return render(request, 'hunt/tag_group.html', context)


def tagger_dashboard(request):
    """
    Dashboard showing tagging statistics for all taggers.
    """
    tagger = get_current_tagger(request)

    # Get all taggers with their stats
    all_taggers = []
    for t in Tagger.objects.all():
        tagger_tags = Tag.objects.filter(tagger=t)
        total = tagger_tags.count()
        unique = tagger_tags.values('group').distinct().count()
        all_taggers.append({
            'tagger': t,
            'total_tags': total,
            'unique_groups': unique,
            'is_current': tagger and t.id == tagger.id,
        })

    # Sort by total tags descending
    all_taggers.sort(key=lambda x: x['total_tags'], reverse=True)

    # Get total stats across all taggers
    total_tags_all = Tag.objects.count()
    total_unique_groups = Tag.objects.values('group').distinct().count()
    total_groups = Group.objects.count()

    # Get recent tags across all taggers
    recent_tags = Tag.objects.select_related('group', 'tagger').order_by('-tagged_at')[:20]

    context = {
        'tagger': tagger,
        'all_taggers': all_taggers,
        'total_tags_all': total_tags_all,
        'total_unique_groups': total_unique_groups,
        'total_groups': total_groups,
        'recent_tags': recent_tags,
    }

    return render(request, 'hunt/tagger_dashboard.html', context)

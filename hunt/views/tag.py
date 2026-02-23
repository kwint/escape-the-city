from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from ..models import Group, Tag


def tag_group(request, group_name: str = None):
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

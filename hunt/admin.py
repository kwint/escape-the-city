from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
import random
from .models import Group, Post, Scan
from .passwords import DUTCH_FOODS


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['scout_group', 'name', 'password', 'created_at', 'scan_count']
    search_fields = ['scout_group', 'name']
    list_filter = ['scout_group', 'created_at']
    readonly_fields = ['created_at']

    def get_fields(self, request, obj=None):
        """Hide password field when adding a new group, show it when editing."""
        if obj is None:
            # Adding new group - hide password field
            return ['scout_group', 'name', 'members', 'phone_number']
        else:
            # Editing existing group - show all fields
            return ['scout_group', 'name', 'password', 'members', 'phone_number', 'created_at']

    def save_model(self, request, obj, form, change):
        """Auto-generate password from Dutch foods list when creating new group."""
        if not change and not obj.password:
            # New group being created - assign random Dutch food as password
            # Get all currently used passwords
            used_passwords = set(Group.objects.values_list('password', flat=True))

            # Find available passwords
            available_passwords = [food for food in DUTCH_FOODS if food not in used_passwords]

            if available_passwords:
                obj.password = random.choice(available_passwords)
            else:
                # All 50 passwords are used, fall back to random with number suffix
                obj.password = f"{random.choice(DUTCH_FOODS)}{random.randint(1, 999)}"
        super().save_model(request, obj, form, change)

    def scan_count(self, obj):
        """Display the number of scans this group has made."""
        count = obj.scans.count()
        return count
    scan_count.short_description = 'Total Scans'


class ScanInline(admin.TabularInline):
    model = Scan
    extra = 0
    readonly_fields = ['group', 'scanned_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'description', 'scan_count', 'scan_page_link', 'qr_code_link', 'created_at']
    list_display_links = ['name']
    list_editable = ['order']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    readonly_fields = ['qr_code_identifier', 'created_at', 'qr_code_preview', 'scan_page_link']
    inlines = [ScanInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'order')
        }),
        ('Instructions', {
            'fields': ('pdf_file',)
        }),
        ('QR Code', {
            'fields': ('qr_code_identifier', 'scan_page_link', 'qr_code_preview'),
            'description': 'Use the "Scan Pagina" link to test the scan page. Use "View QR Code" in the post list to generate and download the QR code.'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def scan_count(self, obj):
        """Display the number of times this post has been scanned."""
        count = obj.scans.count()
        return count
    scan_count.short_description = 'Total Scans'

    def scan_page_link(self, obj):
        """Display a link to the scan page."""
        if obj.pk:
            url = reverse('scan_post', args=[obj.qr_code_identifier])
            return format_html('<a href="{}" target="_blank">Scan Pagina</a>', url)
        return '-'
    scan_page_link.short_description = 'Scan Page'

    def qr_code_link(self, obj):
        """Display a link to generate and view the QR code."""
        if obj.pk:
            url = reverse('generate_qr', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">View QR Code</a>', url)
        return '-'
    qr_code_link.short_description = 'QR Code'

    def qr_code_preview(self, obj):
        """Show the QR code in the admin interface."""
        if obj.pk:
            url = reverse('generate_qr', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px;" /></a><br>'
                '<small>Click to open in new tab</small>',
                url, url
            )
        return '-'
    qr_code_preview.short_description = 'QR Code Preview'


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ['group', 'post', 'scanned_at']
    list_filter = ['scanned_at', 'group', 'post']
    search_fields = ['group__name', 'post__name']
    readonly_fields = ['group', 'post', 'scanned_at']
    date_hierarchy = 'scanned_at'

    def has_add_permission(self, request):
        """Scans should only be created through the public interface."""
        return False


# Customize admin site header
admin.site.site_header = 'Scavenger Hunt Admin'
admin.site.site_title = 'Scavenger Hunt Admin'
admin.site.index_title = 'Manage Your Scavenger Hunt'


# Add custom view link to admin
from django.urls import path
from django.shortcuts import redirect


def admin_index_view(request):
    """Custom admin index that includes overview link."""
    return redirect('/admin/')


# Monkey-patch to add overview link to admin
original_each_context = admin.site.each_context


def custom_each_context(request):
    context = original_each_context(request)
    context['overview_url'] = reverse('overview')
    return context


admin.site.each_context = custom_each_context

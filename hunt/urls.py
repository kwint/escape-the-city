from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path('scan/<uuid:qr_code_identifier>/', views.scan_post, name='scan_post'),
    path('scan/<uuid:qr_code_identifier>/success/<int:group_id>/', views.scan_success, name='scan_success'),
    path('download/<uuid:qr_code_identifier>/<int:group_id>/', views.download_pdf, name='download_pdf'),

    # Tagger URLs
    path('tagger/login/', views.tagger_login, name='tagger_login'),
    path('tagger/logout/', views.tagger_logout, name='tagger_logout'),
    path('tagger/dashboard/', views.tagger_dashboard, name='tagger_dashboard'),
    path('tag/<uuid:qr_code_identifier>/', views.tag_group, name='tag_group'),

    # QR code generation (admin only)
    path('generate-qr/<int:post_id>/', views.generate_qr, name='generate_qr'),
    path('generate-group-qr/<int:group_id>/', views.generate_group_qr, name='generate_group_qr'),
]

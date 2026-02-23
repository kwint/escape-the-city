from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path('scan/<uuid:qr_code_identifier>/', views.scan_post, name='scan_post'),
    path('download/<uuid:qr_code_identifier>/<int:group_id>/', views.download_pdf, name='download_pdf'),
    path('tag/', views.tag_group, name='tag_group'),
    path('tag/<str:group_name', views.tag_group, name='tag_group'),
    path('generate-qr/<int:post_id>/', views.generate_qr, name='generate_qr'),
]

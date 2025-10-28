# repository/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ... (URL lainnya tetap sama) ...
    path('', views.catalog_view, name='catalog'),
    path('dashboard/mahasiswa/', views.dashboard_mahasiswa, name='dashboard_mahasiswa'),
    path('dashboard/dosen/', views.dashboard_dosen, name='dashboard_dosen'),
    path('dashboard/mitra/', views.dashboard_mitra, name='dashboard_mitra'),
    path('dashboard/unit-bisnis/', views.dashboard_unit_bisnis, name='dashboard_unit_bisnis'),
    path('repository/', views.repository_view, name='repository'),
    path('repository/select/<int:project_id>/', views.select_for_curation, name='select_for_curation'),
    path('project/upload/', views.upload_project_view, name='upload_project'),
    path('curation/assign/', views.assign_curator_view, name='assign_curator_list'),
    path('assign-curator/<int:project_id>/', views.handle_assign_curator, name='handle_assign_curator'),
    path('assess/<int:kurasi_id>/', views.assess_project_view, name='assess_project'),
    path('curation/review/', views.review_decision_list_view, name='review_decision_list'),
    path('curation/review/details/<int:kurasi_id>/', views.get_review_details_json, name='get_review_details_json'),
    path('curation/decision/<int:kurasi_id>/', views.handle_project_decision, name='handle_project_decision'),
    path('curation/publish/', views.publish_catalog_list_view, name='publish_catalog_list'),
    path('publish/<int:project_id>/', views.handle_publish_project, name='handle_publish_project'),

    # --- URL BARU UNTUK MONITORING PENILAIAN ---
    path('curation/monitoring/', views.monitoring_penilaian_list_view, name='monitoring_penilaian_list'), # Halaman daftar
    path('curation/monitoring/details/<int:kurasi_id>/', views.get_monitoring_details_json, name='get_monitoring_details_json'), # JSON data for modal
]


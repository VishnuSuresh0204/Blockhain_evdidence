from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

    path('admin/', admin.site.urls),

    path('', views.home),

    path('login/', views.login),

    path('registration/', views.registration),

    path('user_home/', views.user_home),

    path('admin_home/', views.admin_home),

    path('logout/', views.logout),

    path('user_profile/', views.user_profile),

    path('view_users/', views.view_users),

    path('upload_evidence/', views.upload_evidence),

    path('my_evidence/', views.my_evidence),

    path(
        'evidence_details/<int:evidence_id>/',
        views.evidence_details
    ),

    path(
        'verify_evidence/<int:evidence_id>/',
        views.verify_evidence
    ),

    path('admin_evidence/', views.admin_evidence),

    path('blockchain_records/', views.blockchain_records),

    path(
        'verification_history/',
        views.verification_history
    ),
    path('admin_alerts/', views.admin_alerts),
    path('admin_review/<int:evidence_id>/', views.admin_review_evidence),
    path('admin_approve/<int:evidence_id>/', views.admin_approve_evidence),
    path('admin_reject/<int:evidence_id>/', views.admin_reject_evidence),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
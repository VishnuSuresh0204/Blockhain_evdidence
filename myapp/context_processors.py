from .models import AdminAlert, DigitalEvidence

def admin_counts(request):
    if request.session.get('usertype') == 'Admin':
        unread_count = AdminAlert.objects.filter(is_read=False).count()
        pending_review_count = DigitalEvidence.objects.filter(is_modified=True, status='Pending').count()
        return {
            'navbar_unread_alerts': unread_count,
            'navbar_pending_reviews': pending_review_count,
        }
    return {}

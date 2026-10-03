from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .models import *

def home(request):
    return render(request,"home.html")

def user_home(request):
    return render(request,"USER/home.html")


def admin_home(request):
    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    total_users = Registration.objects.count()
    total_evidence = DigitalEvidence.objects.count()
    total_blocks = BlockchainBlock.objects.count()
    total_verifications = EvidenceVerification.objects.count()
    pending_alerts_count = AdminAlert.objects.filter(is_read=False).count()
    pending_reviews_count = DigitalEvidence.objects.filter(is_modified=True, status='Pending').count()
    recent_alerts = AdminAlert.objects.select_related('evidence', 'evidence__user', 'evidence__modified_from').all().order_by('-id')[:5]

    return render(
        request,
        "ADMIN/home.html",
        {
            'total_users': total_users,
            'total_evidence': total_evidence,
            'total_blocks': total_blocks,
            'total_verifications': total_verifications,
            'pending_alerts_count': pending_alerts_count,
            'pending_reviews_count': pending_reviews_count,
            'recent_alerts': recent_alerts,
        }
    )


def login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Django login session
            auth_login(request, user)

            # Your custom sessions
            request.session['userid'] = user.id
            request.session['username'] = user.username
            request.session['usertype'] = user.user_type

            if user.user_type == 'Admin':
                return redirect('/admin_home')

            elif user.user_type == 'User':
                return redirect('/user_home')

            else:
                messages.error(request, 'Invalid user type')
                return redirect('/login')

        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def logout(request):

    auth_logout(request)
    request.session.flush()

    return redirect('/login')



def registration(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')
        profile_image = request.FILES.get('profile_image')

        if Login.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('/registration')

        if Login.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('/registration')

        user = Login.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type='User',
            view_pass=password
        )

        Registration.objects.create(
            user=user,
            name=name,
            email=email,
            phone=phone,
            address=address,
            profile_image=profile_image
        )

        messages.success(request, 'Registration completed successfully')

        return redirect('/login')

    return render(request, 'registration.html')


# ---------------------------------------------------------
# USER PROFILE
# ---------------------------------------------------------

def user_profile(request):

    if 'userid' not in request.session:
        return redirect('/login')

    userid = request.session.get('userid')

    user = Login.objects.get(id=userid)

    profile = Registration.objects.get(user=user)

    if request.method == 'POST':
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if name:
            profile.name = name
        if phone:
            profile.phone = phone
        if address:
            profile.address = address

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('/user_profile/')

    return render(
        request,
        "USER/profile.html",
        {
            'user': user,
            'profile': profile
        }
    )


# ---------------------------------------------------------
# ADMIN - VIEW USERS
# ---------------------------------------------------------

def view_users(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    users = Registration.objects.all().order_by('-id')

    return render(
        request,
        "ADMIN/view_users.html",
        {
            'users': users
        }
    )



# ---------------------------------------------------------
# USER - UPLOAD EVIDENCE
# ---------------------------------------------------------

def upload_evidence(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'User':
        return redirect('/login')

    if request.method == 'POST':

        userid = request.session.get('userid')

        evidence_title = request.POST.get('evidence_title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        evidence_file = request.FILES.get('evidence_file')

        if not evidence_file:
            messages.error(
                request,
                'Please select an evidence file'
            )
            return redirect('/upload_evidence')

        import hashlib

        # -------------------------------------------------
        # SHA-256
        # -------------------------------------------------

        sha256_hash = hashlib.sha256()

        for chunk in evidence_file.chunks():
            sha256_hash.update(chunk)

        file_hash = sha256_hash.hexdigest()

        # -------------------------------------------------
        # EXACT DUPLICATE CHECK
        # -------------------------------------------------

        existing_evidence = DigitalEvidence.objects.filter(
            file_hash=file_hash
        ).first()

        if existing_evidence:

            messages.error(
                request,
                'Duplicate evidence detected! '
                'This exact file has already been uploaded. '
                'Previous Evidence: ' +
                existing_evidence.evidence_title +
                ' | Uploaded On: ' +
                existing_evidence.uploaded_at.strftime(
                    '%d-%m-%Y %I:%M %p'
                )
            )

            return redirect('/upload_evidence')

        # -------------------------------------------------
        # MODIFICATION VARIABLES
        # -------------------------------------------------

        image_hash = None
        is_modified = False
        modified_from = None

        # -------------------------------------------------
        # IMAGE SIMILARITY DETECTION
        # pHash + ORB
        # -------------------------------------------------

        if category == 'Image':

            try:

                from PIL import Image
                import imagehash
                import cv2
                import numpy as np

                # -------------------------------------------------
                # RESET FILE POSITION
                # -------------------------------------------------

                evidence_file.seek(0)

                # -------------------------------------------------
                # pHASH
                # -------------------------------------------------

                image = Image.open(
                    evidence_file
                ).convert('RGB')

                phash = imagehash.phash(image)

                image_hash = str(phash)

                # -------------------------------------------------
                # ORB
                # -------------------------------------------------

                evidence_file.seek(0)

                image_bytes = np.frombuffer(
                    evidence_file.read(),
                    np.uint8
                )

                new_image = cv2.imdecode(
                    image_bytes,
                    cv2.IMREAD_GRAYSCALE
                )

                # If OpenCV cannot read the image,
                # continue without similarity detection.
                if new_image is not None:

                    orb = cv2.ORB_create(
                        nfeatures=1500
                    )

                    new_keypoints, new_descriptors = (
                        orb.detectAndCompute(
                            new_image,
                            None
                        )
                    )

                    similar_evidence = None
                    best_match_count = 0
                    best_phash_difference = None

                    # -------------------------------------------------
                    # GET ALL PREVIOUS IMAGES
                    # -------------------------------------------------

                    previous_images = DigitalEvidence.objects.filter(
                        category='Image'
                    ).exclude(
                        image_hash__isnull=True
                    ).exclude(
                        image_hash=''
                    )

                    # -------------------------------------------------
                    # COMPARE WITH PREVIOUS IMAGES
                    # -------------------------------------------------

                    for old_image in previous_images:

                        try:

                            old_file = (
                                old_image.evidence_file.open(
                                    'rb'
                                )
                            )

                            old_bytes = np.frombuffer(
                                old_file.read(),
                                np.uint8
                            )

                            old_file.close()

                            old_cv_image = cv2.imdecode(
                                old_bytes,
                                cv2.IMREAD_GRAYSCALE
                            )

                            if old_cv_image is None:
                                continue

                            # -------------------------------------------------
                            # OLD IMAGE ORB
                            # -------------------------------------------------

                            old_keypoints, old_descriptors = (
                                orb.detectAndCompute(
                                    old_cv_image,
                                    None
                                )
                            )

                            if (
                                new_descriptors is None
                                or
                                old_descriptors is None
                            ):
                                continue

                            # -------------------------------------------------
                            # FEATURE MATCHING
                            # -------------------------------------------------

                            matcher = cv2.BFMatcher(
                                cv2.NORM_HAMMING,
                                crossCheck=True
                            )

                            matches = matcher.match(
                                new_descriptors,
                                old_descriptors
                            )

                            matches = sorted(
                                matches,
                                key=lambda x: x.distance
                            )

                            # -------------------------------------------------
                            # GOOD MATCHES
                            # -------------------------------------------------

                            good_matches = [
                                match
                                for match in matches
                                if match.distance < 50
                            ]

                            match_count = len(
                                good_matches
                            )

                            # -------------------------------------------------
                            # pHASH COMPARISON
                            # -------------------------------------------------

                            old_phash = imagehash.hex_to_hash(
                                old_image.image_hash
                            )

                            phash_difference = (
                                old_phash - phash
                            )

                            # -------------------------------------------------
                            # STRICT SIMILARITY CHECK
                            #
                            # Both conditions must be satisfied.
                            #
                            # ORB matches >= 30
                            # AND
                            # pHash difference <= 10
                            # -------------------------------------------------

                            if (
                                match_count >= 30
                                and
                                phash_difference <= 10
                            ):

                                # -------------------------------------------------
                                # KEEP BEST MATCH
                                # -------------------------------------------------

                                if (
                                    similar_evidence is None
                                    or
                                    match_count > best_match_count
                                ):

                                    similar_evidence = old_image

                                    best_match_count = (
                                        match_count
                                    )

                                    best_phash_difference = (
                                        phash_difference
                                    )

                        except Exception:
                            continue

                    # -------------------------------------------------
                    # MODIFIED IMAGE DETECTED
                    # -------------------------------------------------

                    if similar_evidence:

                        is_modified = True

                        modified_from = (
                            similar_evidence
                        )

            except Exception:

                image_hash = None

        # -------------------------------------------------
        # GET USER
        # -------------------------------------------------

        user = Login.objects.get(
            id=userid
        )

        # -------------------------------------------------
        # CREATE EVIDENCE
        # -------------------------------------------------

        evidence = DigitalEvidence.objects.create(

            user=user,

            evidence_title=evidence_title,

            description=description,

            category=category,

            evidence_file=evidence_file,

            file_hash=file_hash,

            image_hash=image_hash,

            is_modified=is_modified,

            modified_from=modified_from,

            status='Pending'
        )

        # -------------------------------------------------
        # BLOCKCHAIN
        # -------------------------------------------------

        create_blockchain_block(
            evidence
        )

        # -------------------------------------------------
        # ADMIN ALERT
        # -------------------------------------------------

        if is_modified and modified_from:

            AdminAlert.objects.create(

                evidence=evidence,

                message=(
                    'Modified/Cropped evidence uploaded. '
                    'Evidence "' +
                    evidence.evidence_title +
                    '" uploaded by @' +
                    user.username +
                    ' appears to be a modified version of "' +
                    modified_from.evidence_title +
                    '" uploaded by @' +
                    modified_from.user.username +
                    '. Sent for administrator review.'
                )
            )

        # -------------------------------------------------
        # USER MESSAGE
        # -------------------------------------------------

        if is_modified:

            messages.warning(
                request,
                'Evidence uploaded successfully, but this image '
                'appears to be a cropped or modified version of '
                'previously uploaded evidence: ' +
                modified_from.evidence_title +
                '. The evidence has been flagged for '
                'administrator review.'
            )

        else:

            messages.success(
                request,
                'Evidence uploaded successfully'
            )

        return redirect('/my_evidence')

    return render(
        request,
        "USER/upload_evidence.html"
    )


# ---------------------------------------------------------
# CREATE BLOCKCHAIN BLOCK
# ---------------------------------------------------------

def create_blockchain_block(evidence):

    import hashlib
    import json
    from datetime import datetime

    last_block = BlockchainBlock.objects.order_by(
        '-block_index'
    ).first()

    if last_block:

        block_index = last_block.block_index + 1
        previous_hash = last_block.current_hash

    else:

        block_index = 1
        previous_hash = '0' * 64

    transaction_data = {
        'evidence_id': evidence.id,
        'evidence_title': evidence.evidence_title,
        'file_hash': evidence.file_hash,
        'timestamp': datetime.now().isoformat()
    }

    transaction_string = json.dumps(
        transaction_data,
        sort_keys=True
    )

    block_data = (
        str(block_index) +
        transaction_string +
        previous_hash
    )

    current_hash = hashlib.sha256(
        block_data.encode()
    ).hexdigest()

    BlockchainBlock.objects.create(
        block_index=block_index,
        evidence=evidence,
        transaction_data=transaction_string,
        previous_hash=previous_hash,
        current_hash=current_hash
    )


# ---------------------------------------------------------
# USER - MY EVIDENCE
# ---------------------------------------------------------

def my_evidence(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'User':
        return redirect('/login')

    userid = request.session.get('userid')

    evidence = DigitalEvidence.objects.filter(
        user_id=userid
    ).order_by('-id')

    return render(
        request,
        "USER/my_evidence.html",
        {
            'evidence': evidence
        }
    )


# ---------------------------------------------------------
# USER / ADMIN - EVIDENCE DETAILS
# ---------------------------------------------------------

def evidence_details(request, evidence_id):

    if 'userid' not in request.session:
        return redirect('/login')

    evidence = DigitalEvidence.objects.get(
        id=evidence_id
    )

    blocks = BlockchainBlock.objects.filter(
        evidence=evidence
    ).order_by('block_index')

    return render(
        request,
        "USER/evidence_details.html",
        {
            'evidence': evidence,
            'blocks': blocks
        }
    )

# ---------------------------------------------------------
# VERIFY EVIDENCE
# ---------------------------------------------------------

def verify_evidence(request, evidence_id):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'User':
        return redirect('/login')

    userid = request.session.get('userid')

    evidence = DigitalEvidence.objects.get(
        id=evidence_id,
        user_id=userid
    )

    import hashlib

    sha256_hash = hashlib.sha256()

    with evidence.evidence_file.open('rb') as file:

        for chunk in iter(
            lambda: file.read(4096),
            b''
        ):
            sha256_hash.update(chunk)

    calculated_hash = sha256_hash.hexdigest()

    original_hash = evidence.file_hash

    if calculated_hash == original_hash:

        result = 'Verified'
        evidence.status = 'Verified'

    else:

        result = 'Tampered'
        evidence.status = 'Tampered'

    evidence.save()

    # --------------------------------
    # VERIFICATION HISTORY
    # --------------------------------

    EvidenceVerification.objects.create(

        evidence=evidence,

        verified_by_id=userid,

        original_hash=original_hash,

        calculated_hash=calculated_hash,

        result=result
    )

    # --------------------------------
    # ADMIN ALERT FOR MODIFIED IMAGE
    # --------------------------------

    if evidence.is_modified and evidence.modified_from and not AdminAlert.objects.filter(evidence=evidence).exists():

        AdminAlert.objects.create(

            evidence=evidence,

            message=(
                'Modified/Cropped evidence verified. '
                'Evidence "' +
                evidence.evidence_title +
                '" appears to be a modified version of "' +
                evidence.modified_from.evidence_title +
                '". '
                'The uploaded evidence was flagged for '
                'administrator review.'
            )
        )

    messages.success(
        request,
        'Evidence verification result: ' + result
    )

    return redirect(
        '/evidence_details/' +
        str(evidence.id)
    )

# ---------------------------------------------------------
# ADMIN - ALL EVIDENCE
# ---------------------------------------------------------

def admin_evidence(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    evidence = DigitalEvidence.objects.all().order_by('-id')

    return render(
        request,
        "ADMIN/evidence.html",
        {
            'evidence': evidence
        }
    )


# ---------------------------------------------------------
# ADMIN - BLOCKCHAIN RECORDS
# ---------------------------------------------------------

def blockchain_records(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    blocks = BlockchainBlock.objects.all().order_by(
        'block_index'
    )

    return render(
        request,
        "ADMIN/blockchain.html",
        {
            'blocks': blocks
        }
    )


# ---------------------------------------------------------
# ADMIN - VERIFICATION HISTORY
# ---------------------------------------------------------

def verification_history(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    verifications = EvidenceVerification.objects.all().order_by(
        '-id'
    )

    return render(
        request,
        "ADMIN/verification_history.html",
        {
            'verifications': verifications
        }
    )

# ---------------------------------------------------------
# ADMIN - MODIFICATION ALERTS & TAMPERED EVIDENCE REVIEW
# ---------------------------------------------------------

def admin_alerts(request):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    alerts = AdminAlert.objects.select_related(
        'evidence',
        'evidence__user',
        'evidence__modified_from',
        'evidence__modified_from__user'
    ).all().order_by('-id')

    # All modified evidence for quick reference
    modified_evidences = DigitalEvidence.objects.filter(
        is_modified=True
    ).select_related(
        'user',
        'modified_from',
        'modified_from__user'
    ).order_by('-id')

    return render(
        request,
        "ADMIN/admin_alerts.html",
        {
            'alerts': alerts,
            'modified_evidences': modified_evidences,
        }
    )


# ---------------------------------------------------------
# ADMIN - SIDE-BY-SIDE TAMPERED EVIDENCE REVIEW
# ---------------------------------------------------------

def admin_review_evidence(request, evidence_id):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    evidence = DigitalEvidence.objects.select_related('user', 'modified_from', 'modified_from__user').get(
        id=evidence_id
    )

    original_evidence = evidence.modified_from

    # Fetch uploader profiles
    tampered_profile = Registration.objects.filter(user=evidence.user).first()
    original_profile = (
        Registration.objects.filter(user=original_evidence.user).first()
        if original_evidence else None
    )

    # Dynamic image similarity metrics calculation
    match_metrics = {
        'phash_difference': None,
        'orb_matches': None,
        'similarity_verdict': None,
    }

    if (
        original_evidence and
        evidence.category == 'Image' and
        original_evidence.category == 'Image'
    ):
        try:
            from PIL import Image
            import imagehash
            import cv2
            import numpy as np

            # pHash calculation
            with evidence.evidence_file.open('rb') as f1, original_evidence.evidence_file.open('rb') as f2:
                img1 = Image.open(f1).convert('RGB')
                img2 = Image.open(f2).convert('RGB')
                h1 = imagehash.phash(img1)
                h2 = imagehash.phash(img2)
                match_metrics['phash_difference'] = abs(h1 - h2)

            # ORB Feature calculation
            with evidence.evidence_file.open('rb') as f1, original_evidence.evidence_file.open('rb') as f2:
                b1 = np.frombuffer(f1.read(), np.uint8)
                b2 = np.frombuffer(f2.read(), np.uint8)
                cv1 = cv2.imdecode(b1, cv2.IMREAD_GRAYSCALE)
                cv2_img = cv2.imdecode(b2, cv2.IMREAD_GRAYSCALE)
                if cv1 is not None and cv2_img is not None:
                    orb = cv2.ORB_create(nfeatures=1500)
                    kp1, des1 = orb.detectAndCompute(cv1, None)
                    kp2, des2 = orb.detectAndCompute(cv2_img, None)
                    if des1 is not None and des2 is not None:
                        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        matches = matcher.match(des1, des2)
                        good_matches = [m for m in matches if m.distance < 50]
                        match_metrics['orb_matches'] = len(good_matches)

            # Formulate verdict summary
            p_diff = match_metrics['phash_difference']
            o_cnt = match_metrics['orb_matches']
            if p_diff is not None and o_cnt is not None:
                if p_diff <= 10 or o_cnt >= 15:
                    match_metrics['similarity_verdict'] = f"High Similarity Detected ({o_cnt} ORB matches, pHash diff: {p_diff})"
                else:
                    match_metrics['similarity_verdict'] = f"Moderate/Low Similarity ({o_cnt} ORB matches, pHash diff: {p_diff})"
        except Exception:
            pass

    # Mark related alerts as read since admin is reviewing
    AdminAlert.objects.filter(evidence=evidence).update(is_read=True)

    blocks = BlockchainBlock.objects.filter(evidence=evidence).order_by('block_index')

    return render(
        request,
        "ADMIN/admin_review.html",
        {
            'evidence': evidence,
            'original_evidence': original_evidence,
            'tampered_profile': tampered_profile,
            'original_profile': original_profile,
            'match_metrics': match_metrics,
            'blocks': blocks,
        }
    )


# ---------------------------------------------------------
# ADMIN - APPROVE EVIDENCE
# ---------------------------------------------------------

def admin_approve_evidence(request, evidence_id):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    evidence = DigitalEvidence.objects.get(id=evidence_id)
    evidence.status = 'Approved'
    evidence.save()

    AdminAlert.objects.filter(evidence=evidence).update(is_read=True)

    messages.success(
        request,
        f'Evidence #{evidence.id} ("{evidence.evidence_title}") has been APPROVED.'
    )

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(f'/admin_review/{evidence.id}/')


# ---------------------------------------------------------
# ADMIN - REJECT EVIDENCE
# ---------------------------------------------------------

def admin_reject_evidence(request, evidence_id):

    if 'userid' not in request.session:
        return redirect('/login')

    if request.session.get('usertype') != 'Admin':
        return redirect('/login')

    evidence = DigitalEvidence.objects.get(id=evidence_id)
    evidence.status = 'Rejected'
    evidence.save()

    AdminAlert.objects.filter(evidence=evidence).update(is_read=True)

    messages.warning(
        request,
        f'Evidence #{evidence.id} ("{evidence.evidence_title}") has been REJECTED.'
    )

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(f'/admin_review/{evidence.id}/')

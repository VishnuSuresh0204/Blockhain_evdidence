from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .models import *

def home(request):
    return render(request,"home.html")

def user_home(request):
    return render(request,"USER/home.html")


def admin_home(request):
    return render(request,"ADMIN/home.html")


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

        # --------------------------------
        # SHA-256
        # --------------------------------

        sha256_hash = hashlib.sha256()

        for chunk in evidence_file.chunks():
            sha256_hash.update(chunk)

        file_hash = sha256_hash.hexdigest()

        # --------------------------------
        # EXACT DUPLICATE CHECK
        # Checks ALL USERS
        # --------------------------------

        existing_evidence = DigitalEvidence.objects.filter(
            file_hash=file_hash
        ).first()

        if existing_evidence:

            messages.error(
                request,
                'Duplicate evidence detected! '
                'This exact file was already uploaded. '
                'Previous Evidence: ' +
                existing_evidence.evidence_title +
                ' | Uploaded On: ' +
                existing_evidence.uploaded_at.strftime(
                    '%d-%m-%Y %I:%M %p'
                )
            )

            return redirect('/upload_evidence')

        # --------------------------------
        # IMAGE pHASH CHECK
        # Checks ALL USERS
        # --------------------------------

        image_hash = None

        if category == 'Image':

            try:

                from PIL import Image
                import imagehash

                # Generate pHash
                image = Image.open(evidence_file)

                image_hash = str(
                    imagehash.phash(image)
                )

                new_hash = imagehash.hex_to_hash(
                    image_hash
                )

                similar_evidence = None
                similarity_difference = None

                # Get ALL previously uploaded images
                previous_images = DigitalEvidence.objects.filter(
                    category='Image'
                ).exclude(
                    image_hash__isnull=True
                ).exclude(
                    image_hash=''
                )

                # Compare with every previous image
                for old_image in previous_images:

                    old_hash = imagehash.hex_to_hash(
                        old_image.image_hash
                    )

                    difference = old_hash - new_hash

                    # Stronger threshold
                    if difference <= 15:

                        similar_evidence = old_image
                        similarity_difference = difference

                        break

                # --------------------------------
                # MODIFIED IMAGE DETECTED
                # --------------------------------

                if similar_evidence:

                    messages.error(
                        request,
                        'Modified image detected! '
                        'This image appears to be a modified '
                        'or cropped version of previously uploaded evidence. '
                        'Previous Evidence: ' +
                        similar_evidence.evidence_title +
                        ' | Uploaded On: ' +
                        similar_evidence.uploaded_at.strftime(
                            '%d-%m-%Y %I:%M %p'
                        ) +
                        ' | Similarity Distance: ' +
                        str(similarity_difference)
                    )

                    return redirect('/upload_evidence')

            except Exception as e:

                image_hash = None

        # --------------------------------
        # CREATE NEW EVIDENCE
        # --------------------------------

        user = Login.objects.get(
            id=userid
        )

        evidence = DigitalEvidence.objects.create(
            user=user,
            evidence_title=evidence_title,
            description=description,
            category=category,
            evidence_file=evidence_file,
            file_hash=file_hash,
            image_hash=image_hash,
            status='Pending'
        )

        # --------------------------------
        # CREATE BLOCKCHAIN BLOCK
        # --------------------------------

        create_blockchain_block(
            evidence
        )

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

    EvidenceVerification.objects.create(
        evidence=evidence,
        verified_by_id=userid,
        original_hash=original_hash,
        calculated_hash=calculated_hash,
        result=result
    )

    messages.success(
        request,
        'Evidence verification result: ' + result
    )

    return redirect(
        '/evidence_details/' + str(evidence.id)
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
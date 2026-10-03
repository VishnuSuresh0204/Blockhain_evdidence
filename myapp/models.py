from django.db import models
from django.contrib.auth.models import AbstractUser


class Login(AbstractUser):
    user_type = models.CharField(max_length=50)
    view_pass = models.CharField(max_length=255)

    def __str__(self):
        return self.username


class Registration(models.Model):
    user = models.ForeignKey(
        Login,
        on_delete=models.CASCADE,
        related_name='registration'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DigitalEvidence(models.Model):
    CATEGORY_CHOICES = [
        ('Image', 'Image'),
        ('Video', 'Video'),
        ('Audio', 'Audio'),
        ('Document', 'Document'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Tampered', 'Tampered'),
    ]

    user = models.ForeignKey(
        Login,
        on_delete=models.CASCADE,
        related_name='evidence'
    )
    evidence_title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    evidence_file = models.FileField(upload_to='evidence/')
    file_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.evidence_title


class BlockchainBlock(models.Model):
    block_index = models.PositiveIntegerField()
    evidence = models.ForeignKey(
        DigitalEvidence,
        on_delete=models.CASCADE,
        related_name='blockchain_blocks'
    )
    transaction_data = models.TextField()
    previous_hash = models.CharField(max_length=64)
    current_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Block {self.block_index}"


class EvidenceVerification(models.Model):
    evidence = models.ForeignKey(
        DigitalEvidence,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    verified_by = models.ForeignKey(
        Login,
        on_delete=models.CASCADE,
        related_name='evidence_verifications'
    )
    original_hash = models.CharField(max_length=64)
    calculated_hash = models.CharField(max_length=64)
    result = models.CharField(max_length=20)
    verified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evidence.evidence_title} - {self.result}"
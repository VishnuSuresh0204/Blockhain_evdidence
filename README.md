ABSTRACT

The Blockchain-Based Digital Evidence Management System is a secure web-based application developed to manage, preserve, verify, and monitor digital evidence such as images, videos, audio files, and documents. The system is designed to improve the integrity, traceability, and accountability of digital evidence throughout its management lifecycle. Users can register, maintain their profiles, and upload digital evidence with relevant details. When evidence is uploaded, the system generates a unique SHA-256 cryptographic hash for the file and stores the hash along with the evidence details. A hash-linked blockchain ledger is also created to maintain an immutable-style audit record of evidence transactions.

The proposed system additionally provides image similarity detection using pHash and ORB techniques. When a new image is uploaded, it is compared with previously stored images to identify potentially similar, cropped, or modified versions. Exact duplicate files are detected using SHA-256 and prevented from being uploaded again, while potentially modified images are stored as separate evidence and linked to the original evidence. Such evidence is automatically flagged and sent to the administrator for review instead of being automatically rejected.

Administrators can monitor registered users, uploaded evidence, blockchain records, verification history, and modification alerts. They can compare the original and modified evidence, examine similarity information, and approve or reject flagged evidence. The system also provides SHA-256-based integrity verification, where the currently calculated hash is compared with the originally stored hash to identify whether the stored evidence file has changed. Thus, the system combines digital evidence management, cryptographic integrity verification, image similarity analysis, blockchain-based audit logging, and administrator review into a single platform.

EXISTING SYSTEM

In the existing system, digital evidence is generally managed using conventional file storage or database-based applications. Evidence files and their associated information are stored in a centralized database or file system without a strong mechanism for maintaining an immutable audit trail.

The major limitations of the existing system are:

Digital evidence is mainly stored as ordinary files.
File integrity may not be continuously verified.
Detecting duplicate evidence is difficult.
Modified or cropped images may not be automatically identified.
There is limited relationship tracking between original and modified evidence.
Evidence activities may not have a reliable hash-linked audit record.
Manual verification can be time-consuming.
Administrator monitoring of suspicious evidence is limited.
Changes to stored evidence may be difficult to identify.
Evidence review and approval may not be systematically recorded.
PROPOSED SYSTEM

The proposed system provides a centralized web-based platform for securely managing digital evidence using SHA-256 hashing, image similarity detection, and a blockchain-style hash-linked ledger.

The user can register and upload digital evidence along with its title, description, category, and file. During upload, the system generates a SHA-256 hash of the file. If the same file has already been uploaded, the system identifies it as an exact duplicate and prevents duplicate storage.

For image evidence, the system additionally calculates a perceptual hash (pHash) and extracts visual features using ORB (Oriented FAST and Rotated BRIEF). The new image is compared with previously stored images. If strong similarity is detected, the image is stored as a new evidence record but marked as potentially modified or cropped and linked to the related original evidence.

Each uploaded evidence record also creates a block in the application's hash-linked blockchain ledger. Each block contains the evidence information, file hash, previous block hash, current block hash, and timestamp. This provides a traceable audit structure for the evidence records.

The administrator receives alerts for potentially modified evidence and can review the original and new evidence, examine pHash and ORB similarity information, and make an Approve or Reject decision. The system also maintains verification history whenever SHA-256 integrity verification is performed.

ENTITIES AND THEIR FUNCTIONS
1. Login Entity

Purpose:
Stores authentication and role information for system users and administrators.

Main fields
id
username
email
password
user_type
view_pass
Functions
User login
Administrator login
Authentication
Role identification
Session management
Logout
User access control
2. Registration Entity

Purpose:
Stores the personal and profile information of registered users.

Main fields
user
name
email
phone
address
profile_image
created_at
Functions
User registration
Store user profile
Update profile information
Upload profile image
Maintain registered-user information
3. DigitalEvidence Entity

Purpose:
Stores the actual digital evidence and its security and verification information.

Main fields
user
evidence_title
description
category
evidence_file
file_hash
image_hash
is_modified
modified_from
status
uploaded_at
Functions
Upload digital evidence
Store evidence metadata
Store evidence file
Generate and store SHA-256 hash
Generate image pHash
Detect potentially similar/modified images
Link modified evidence with original evidence
Maintain evidence status
View evidence
Support evidence verification
4. BlockchainBlock Entity

Purpose:
Maintains the hash-linked blockchain-style audit record for uploaded evidence.

Main fields
block_index
evidence
transaction_data
previous_hash
current_hash
timestamp
Functions
Create blockchain block
Store evidence transaction
Maintain previous block hash
Generate current block hash
Maintain chronological evidence records
Support blockchain integrity validation
Provide an audit trail
5. EvidenceVerification Entity

Purpose:
Stores the history of SHA-256 integrity verification operations.

Main fields
evidence
verified_by
original_hash
calculated_hash
result
verified_at
Functions
Store verification request
Store original SHA-256 hash
Store newly calculated SHA-256 hash
Compare hashes
Record Verified or Tampered
Maintain verification history
Identify changes in evidence files
6. AdminAlert Entity

Purpose:
Stores alerts generated when potentially modified or cropped evidence is detected.

Main fields
evidence
message
is_read
created_at
Functions
Generate modification alerts
Notify administrator
Store alert message
Track read/unread status
Connect suspicious evidence with Admin review
Maintain alert history
MODULES
1. User Management Module
Functions
User registration
Login
Logout
Profile management
Profile image upload
Session-based authentication
2. Digital Evidence Management Module
Functions
Upload evidence
Select evidence category
Add evidence title and description
Store evidence file
View uploaded evidence
View evidence details
Prevent exact duplicate files
3. Cryptographic Integrity Module
Technology

SHA-256

Functions
Generate SHA-256 hash
Identify exact duplicate files
Store original file hash
Recalculate hash during verification
Compare original and calculated hashes
Mark evidence as Verified or Tampered
4. Image Similarity Detection Module
Technologies
pHash
ORB
OpenCV
Functions
Generate perceptual hash
Extract image features
Compare newly uploaded images with previous images
Detect potentially similar images
Identify potentially cropped/modified versions
Link modified evidence with original evidence
Send suspicious evidence for Admin review

This is image analysis, rather than a trained ML model. pHash and ORB are computer-vision techniques used to identify visual similarity.

5. Blockchain Audit Module
Technology

Python SHA-256 hash-linked blockchain

Functions
Create blocks
Generate block hash
Store previous block hash
Link blocks sequentially
Store evidence transaction data
Maintain timestamp
Validate blockchain records
Detect changes in the hash chain
6. Admin Review Module
Functions
View modification alerts
View flagged evidence
View original evidence
View modified evidence
Compare evidence information
View pHash difference
View ORB match count
Review blockchain information
Approve evidence
Reject evidence
Mark alerts as read
7. Evidence Verification History Module
Functions
Record every verification
Store original hash
Store calculated hash
Store verification result
Store verifier information
Store verification timestamp
View verification history
SECURITY / AI COMPONENT

Your project has three main technical intelligence/security components:

Component	Purpose
SHA-256	File integrity and exact duplicate detection
pHash	Perceptual image similarity
ORB + OpenCV	Visual feature matching between images
Blockchain hash chain	Evidence audit trail and tamper-evident record structure

The pHash + ORB part should be described as image similarity detection/computer vision, not as a machine-learning model. This makes your project description technically accurate.

Overall System Flow
User Registration/Login
        ↓
Upload Digital Evidence
        ↓
Generate SHA-256
        ↓
Exact Duplicate Check
   ┌───────────────┐
   │               │
 Duplicate       New File
   │               │
 Reject             ↓
              Image?
             /      \
           No        Yes
           ↓          ↓
        Store     pHash + ORB
                      ↓
              Similarity Detection
                 /          \
              Normal       Similar
                ↓             ↓
             Pending     Modified = True
                              ↓
                        Link to Original
                              ↓
                         Admin Alert
                              ↓
                         Admin Review
                         /          \
                    Approve        Reject

Alongside this:

Evidence
   ↓
Blockchain Block
   ↓
Previous Hash
   ↓
Current Hash
   ↓
Audit Trail

And for integrity verification:

Stored SHA-256
      ↓
Calculate Current SHA-256
      ↓
Compare
   /       \
Same     Different
 ↓           ↓
Verified   Tampered

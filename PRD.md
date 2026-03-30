# Product Requirements Document (PRD)
## Real Estate Platform - PropDZ

**Version:** 1.0  
**Last Updated:** March 16, 2026  
**Status:** Production Ready ✅

---

## 1. EXECUTIVE SUMMARY

PropDZ is a full-featured Django-based real estate platform that connects property sellers, landlords, and renters. The platform enables users to list properties, search available properties, inquire about listings, and manage reservations/bookings. It includes a comprehensive admin panel for staff to manage content, users, and platform operations.

**Key Statistics:**
- **6 Django Apps** (accounts, listings, messaging, dashboard, admin_panel, core)
- **6 Database Models** (CustomUser, Property, PropertyImage, ContactMessage, Inquiry, Reservation, InquiryMessage)
- **25+ Views** handling all business logic
- **12+ Forms** for data input validation
- **40+ URL Routes** covering all features
- **25+ HTML Templates** with responsive Bootstrap 5 design
- **500+ Lines of CSS** custom styling

---

## 2. PRODUCT OVERVIEW

### 2.1 Core Modules

#### **Module 1: Authentication & User Management (accounts/)**
Handles user registration, login, profile management, and account security.

#### **Module 2: Property Listings (listings/)**
Complete CRUD operations for real estate properties with advanced search and filtering.

#### **Module 3: Messaging System (messaging/)**
Enables communication between buyers/renters and property owners through inquiries and reservations.

#### **Module 4: User Dashboard (dashboard/)**
Personal dashboard for users to manage their listings, inquiries, and reservations.

#### **Module 5: Admin Panel (admin_panel/)**
Staff control panel for managing properties, users, inquiries, and system-wide settings.

#### **Module 6: Core Utilities (core/)**
Shared mixins, context processors, and reusable components.

---

## 3. USER ROLES & PERMISSIONS

### 3.1 User Types

| Role | Description | Capabilities |
|------|-------------|--------------|
| **Anonymous User** | Not logged in | View listings, property details, contact form |
| **Regular User** | Registered, not staff | Create listings, inquire about properties, make reservations, manage own profile |
| **Staff/Admin** | `is_staff=True` | Access admin panel, approve listings, manage users, ban accounts, view all inquiries |
| **Superuser** | Full Django admin | Django admin access + all staff capabilities |
| **Banned User** | `is_banned=True` | Cannot login (active check enforced) |

### 3.2 Permission Matrix

| Feature | Anonymous | User | Admin | Superuser |
|---------|----------|------|-------|-----------|
| View Home | ✅ | ✅ | ✅ | ✅ |
| View Listings | ✅ | ✅ | ✅ | ✅ |
| Create Listing | ❌ | ✅ | ✅ | ✅ |
| Edit Own Listing | ❌ | ✅ | ✅ | ✅ |
| Delete Own Listing | ❌ | ✅ | ✅ | ✅ |
| Inquire Property | ❌ | ✅ | ✅ | ✅ |
| View Dashboard | ❌ | ✅ | ✅ | ✅ |
| View Inbox | ❌ | ✅ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ✅ | ✅ |
| Approve Listings | ❌ | ❌ | ✅ | ✅ |
| Ban Users | ❌ | ❌ | ✅ | ✅ |
| Delete Users | ❌ | ❌ | ✅ | ✅ |
| Django Admin | ❌ | ❌ | ❌ | ✅ |

---

## 4. CORE FEATURES & FUNCTIONALITY

### 4.1 Authentication System

#### 4.1.1 User Registration
- **Endpoint:** `POST /accounts/register/`
- **Form Fields:** 
  - Username (unique)
  - Email (unique)
  - First Name
  - Last Name
  - Password (min 8 characters)
  - Password Confirmation
- **Validation:**
  - Minimum password length: 8 characters
  - Password confirmation match
  - Unique username and email
  - No account similarity validation
- **Post-Registration:**
  - User account created as inactive
  - Auto-login user after successful registration
  - Redirect to dashboard

#### 4.1.2 User Login
- **Endpoint:** `POST /accounts/login/`
- **Authentication:**
  - Support login via **username OR email**
  - Rate limiting: 5 attempts per minute per IP
  - Ban check: Banned users cannot login
- **Features:**
  - "Remember me" functionality (optional)
  - Redirect to next page or dashboard after login
  - Error messages for invalid credentials

#### 4.1.3 User Logout
- **Endpoint:** `POST /accounts/logout/`
- **Action:** Clear session, redirect to home

#### 4.1.4 Password Reset
- **Endpoint:** `GET/POST /accounts/password-reset/`
- **Flow:**
  1. User enters email
  2. Django sends password reset token via email
  3. User clicks link in email
  4. User sets new password
  5. Redirect to login
- **Token Validity:** Default Django (1 hour)

#### 4.1.5 Profile Management
- **Endpoint:** `GET/POST /accounts/profile/`
- **Fields:**
  - First Name
  - Last Name
  - Email
  - Phone Number
  - Bio/About Me
  - Avatar (optional)
- **Restrictions:**
  - Email must be unique
  - Phone format validation
- **Auth Required:** Yes (LoginRequiredMixin)

### 4.2 Property Listings System

#### 4.2.1 List Properties (Browse)
- **Endpoint:** `GET /listings/`
- **Display:**
  - Paginated list (12-25 items per page)
  - Property cards with primary image, title, price, city
  - View count badge
  - Status badge
- **Filtering:**
  - By property type (Sale, Rent, Vacation)
  - By category (Apartment, Villa, Land, Commercial)
  - By city (search)
  - By price range (min-max)
  - By featured status
- **Sorting:**
  - Latest first (default)
  - Price: Low to High
  - Price: High to Low
  - Most Viewed
- **Search:**
  - Full-text search using PostgreSQL SearchVector
  - Searches: title, description, city
  - Ranked by relevance

#### 4.2.2 View Property Details
- **Endpoint:** `GET /listings/<slug>/`
- **Display:**
  - Full property information
  - Image gallery (all images with primary image highlighted)
  - Price and key features (area, rooms, bathrooms, floor)
  - Furnished and parking status
  - Owner contact information
  - View count
  - Inquiry form (for logged-in users)
  - Reservation form (for logged-in users)
- **View Tracking:**
  - Increments `views_count` on each unique user visit
  - Stores user in `viewed_by` ManyToMany field
  - Atomic increment for race-condition safety

#### 4.2.3 Create Property Listing
- **Endpoint:** `GET/POST /listings/new/`
- **Auth Required:** Yes (LoginRequiredMixin)
- **Form Fields:**
  - Title (max 200 chars)
  - Description (TextField)
  - Property Type (dropdown: Sale, Rent, Vacation)
  - Category (dropdown: Apartment, Villa, Land, Commercial)
  - Price (decimal, min 0)
  - City (indexed for quick search)
  - Address
  - Area (m²) - optional
  - Number of Rooms - optional
  - Number of Bathrooms - optional
  - Floor Number - optional
  - Furnished (checkbox)
  - Parking (checkbox)
  - Primary Image
  - Additional Images (up to 10, formset)
  - Featured (admin only, checkbox)
- **Process:**
  1. User fills form with images
  2. Slug auto-generated from title (handles conflicts)
  3. Status set to 'pending'
  4. Property saved
  5. Formset images saved
  6. Redirect to dashboard
- **Image Validation:**
  - Max file size: 10MB per image
  - Allowed types: JPG, PNG, GIF, WebP
  - Max 10 images per property
  - One image marked as primary

#### 4.2.4 Edit Property Listing
- **Endpoint:** `GET/POST /listings/<slug>/edit/`
- **Auth Required:** Yes (OwnerRequiredMixin)
- **Restrictions:**
  - Only property owner can edit
  - Returns Http404 if not owner
- **Fields:** Same as creation
- **Process:**
  1. Load existing data
  2. Allow modification
  3. Handle image uploads/removals
  4. Update slug if title changed
  5. Preserve other fields
  6. Redirect to property detail

#### 4.2.5 Delete Property Listing
- **Endpoint:** `POST /listings/<slug>/delete/`
- **Auth Required:** Yes (OwnerRequiredMixin)
- **Action:**
  - Hard delete from database
  - Cascade delete associated images and reservations
  - Redirect to dashboard
- **Confirmation:** Required via form submission

#### 4.2.6 Property Status Workflow
```
pending → (admin approval) → active → (user action) → sold/rented/reserved
                         ↓ (admin rejection)
                       refused
                         ↓
                       deleted (soft delete via status)
```

**Status Options:**
| Status | Display | Visibility | Action |
|--------|---------|------------|--------|
| pending | Warning (Yellow) | Not public | Awaiting admin approval |
| active | Success (Green) | Public searchable | Available for inquiry |
| reserved | Info (Blue) | Shown but not available | Reservation in progress |
| sold | Danger (Red) | Not available | No longer available |
| rented | Info (Blue) | Not available | Currently rented |
| refused | Secondary (Gray) | Hidden | Rejected by admin |
| deleted | Secondary (Gray) | Hidden | Soft deleted |

---

### 4.3 Messaging & Communication System

#### 4.3.1 Contact Form
- **Endpoint:** `POST /contact/`
- **Fields:**
  - Name
  - Email
  - Phone (optional)
  - Subject
  - Message
- **Recipient:** Admin inbox
- **Notification:** Admin can view in admin panel
- **No Authentication Required**

#### 4.3.2 Property Inquiry
- **Endpoint:** `POST /listings/<slug>/inquiry/`
- **Auth Required:** Yes (LoginRequiredMixin)
- **Trigger:**
  - User clicks "Inquire" on property detail page
  - Creates conversation with property owner
- **Fields:**
  - Initial message (required)
- **Validation:**
  - Cannot inquire about own property
  - Recipient automatically set to property owner
- **Data Created:**
  - Inquiry record (connects buyer, seller, property)
  - Initial message stored in Inquiry.message
  - `from_user` = inquirer, `to_user` = property owner
- **Read Status:**
  - `to_user_read = False` until owner reads inquiry
  - Marks as unread notification for owner

#### 4.3.3 Inquiry Messages (Chat)
- **Endpoint:** `POST /dashboard/inbox/<inquiry_id>`
- **Auth Required:** Yes (LoginRequiredMixin)
- **Functionality:**
  - Reply to initial inquiry message
  - Back-and-forth communication between buyer and seller
  - Messages displayed in conversation thread
  - Threaded by Inquiry ID
- **Message Storage:**
  - Stored in InquiryMessage model
  - Linked to parent Inquiry
  - Ordered by creation time (oldest first)
- **Auto-Scroll:**
  - JavaScript auto-scrolls to last message on page load
  - Auto-scrolls when conversation expanded
- **Message Styling:**
  - Inquirer messages: Light blue background (#e3f2fd)
  - Owner messages: Light green background (#e8f5e9)
  - Left border accent (blue for inquirer, green for owner)
  - Sender name in matching color

#### 4.3.4 Reservation System
- **Endpoint:** `POST /listings/<slug>/reserve/`
- **Auth Required:** Yes (LoginRequiredMixin)
- **Functionality:**
  - Create rental/booking request for property
  - Set check-in and check-out dates
  - Optional message to owner
- **Fields:**
  - Check-in Date (DateField)
  - Check-out Date (DateField)
  - Message (optional)
- **Validation:**
  - Cannot reserve own property
  - Check-out date must be after check-in date
  - Date range must be valid (check model clean())
- **Status Workflow:**
  ```
  pending (sent) → confirmed (owner accepts) → deal_done
                ↓
              rejected (owner declines) → removed from user dashboard (soft delete)
  ```
- **Soft Delete for Guests:**
  - When guest deletes reservation from their dashboard:
    - Sets `deleted_for_guest_at = timezone.now()`
    - Guest no longer sees it
  - When owner deletes property:
    - Hard deletes all cascading reservations
  - When owner rejects reservation:
    - Hard delete for confirmed reservations
    - For rejected: hard delete
- **Owner Sees:**
  - All reservations for their properties
  - Including soft-deleted ones (deleted_for_guest_at is set but owner still sees)

---

### 4.4 User Dashboard

#### 4.4.1 Overview Tab
- **Endpoint:** `GET /dashboard/`
- **Auth Required:** Yes (LoginRequiredMixin)
- **Display Cards:**

| Card | Shows | Calculation |
|------|-------|-------------|
| My Listings | Count | `Property.objects.filter(owner=user).count()` |
| | Active Listings | `status='active'` subset |
| Inquiries | Total Messages | All InquiryMessage from inquiries where user is `to_user OR from_user` |
| | Unread | Same as sidebar count |
| Reservations | Total Count | `Reservation.objects.filter(from_user=user) + Reservation.objects.filter(to_user=user)` |

**Statistics Section:**
- Recent Listings (6 most recent, with status badges)
- Recent Inquiries (6 most recent, shows property & message preview)

#### 4.4.2 My Listings Tab
- **Endpoint:** `GET /dashboard/listings/`
- **Display:**
  - List of user's properties
  - Filters: All, Pending, Active, Sold, Rented
  - Actions: Edit, Delete, View
  - Status badges
  - Created date display
  - View count
- **Pagination:** 12-25 items per page
- **Features:**
  - Bulk actions ready (not implemented yet)
  - Inline editing indicators

#### 4.4.3 My Inbox Tab
- **Endpoint:** `GET /dashboard/inbox/`
- **Display:**
  - List of all inquiries (both sent and received)
  - Sort by most recent
  - Expandable conversation cards
  - Unread indicators
- **Per Inquiry:**
  - Inquirer name with "Owner" or "Inquirer" badge
  - Property being inquired about
  - Message preview (truncated)
  - Date received
  - **Action Buttons:**
    - **View Property** (eye icon) - Opens property detail
    - **Request Reservation** (calendar icon) - Only visible to inquirers (clients who sent inquiry)
    - **Delete** (trash icon) - Removes conversation from inbox
  
**Conversation Thread:**
  - Initial inquiry message
  - Follow-up messages in chronological order
  - Color-coded by sender (blue for inquirer, green for owner)
  - Sender name displayed above each message
  - Timestamp for each message
  - Chat box with max-height 350px, auto-scrollable
  - Reply form at bottom

**Message Features:**
  - New message indicator
  - Auto-scroll to last message on page load
  - Auto-scroll when conversation expanded
  - Two-sided colors (inquirer blue, owner green)
  - Left border accent (#2196F3 for blue, #4CAF50 for green)

#### 4.4.4 My Reservations Tab
- **Endpoint:** `GET /dashboard/reservations/`
- **Display:**
  - Reservations made by user (as guest)
  - Reservations received (as property owner)
  - Status: Pending, Confirmed, Rejected, Cancelled
  - Check-in and check-out dates
  - Actions: View, Message Owner, Cancel
- **Pagination:** 12-25 per page

#### 4.4.5 Dashboard Utilities Function
```python
def get_dashboard_context(user):
    """
    Returns all dashboard counters for consistent display.
    Used across all dashboard views.
    """
    return {
        'my_listings_count': Property count for owner=user
        'active_listings_count': status='active' subset
        'pending_listings_count': status='pending' subset
        'unread_inquiries_count': New inquiries + unread messages
        'total_inquiries_count': All inquiries where to_user=user OR from_user=user
        'total_messages_count': All InquiryMessage
        'pending_reservations_count': Reservations awaiting response
        'total_reservations_count': All user reservations
        'total_received_reservations_count': Reservations for user's properties
    }
```

---

### 4.5 Admin Panel

#### 4.5.1 Admin Panel Overview
- **Base URL:** `/admin-panel/`
- **Auth Required:** `is_staff=True` (StaffRequiredMixin)
- **Main Dashboard:**
  - Total statistics
  - Recent activity
  - Pending items count
  - Tab navigation to sub-managers

#### 4.5.2 Listings Manager
- **URL:** `/admin-panel/listings/`
- **Display:**
  - All properties regardless of owner
  - Filter by status (Pending, Active, Sold, Rented, Refused)
  - Pagination
  - Image thumbnail preview
  - Price and details display
- **Actions:**
  - **Approve:** Change status from 'pending' to 'active'
  - **Reject:** Change status to 'refused'
  - **View:** Open property detail in new tab
  - **Delete:** Hard delete property (with image cleanup)
- **Status Badges:** Color-coded (warning, success, info, danger, secondary)

#### 4.5.3 Users Manager
- **URL:** `/admin-panel/users/`
- **Display:**
  - All registered users
  - Join date, email, activity
  - User type indicator (Regular/Staff)
- **Actions for Regular Users:**
  - **Ban:** Set `is_banned=True` (user cannot login)
  - **Unban:** Set `is_banned=False`
  - **Delete:** Remove user account
- **Actions for Staff/Admins:**
  - **Delete:** Remove admin account with logout
  - (Cannot ban admins for security)
- **Security:**
  - Admins cannot delete themselves
  - Message displayed when trying self-delete
  - Automatic logout when admin account deleted (session removal)

#### 4.5.4 Contacts Inbox
- **URL:** `/admin-panel/contacts/`
- **Display:**
  - All contact form submissions
  - Sender name, email, phone
  - Subject and message preview
  - Date received
  - Read/Unread status
- **Actions:**
  - **Mark as Read:** Click to toggle
  - **Delete:** Remove contact message
  - **Reply:** (Email functionality - can be expanded)

#### 4.5.5 Reservations Manager
- **URL:** `/admin-panel/reservations/`
- **Display:**
  - All reservations system-wide
  - Filter by status
  - Property details
  - Guest and owner information
  - Check-in and check-out dates
- **Actions:**
  - **Confirm:** Move from pending to confirmed
  - **Reject:** Move to rejected status
  - **Cancel:** Move to cancelled
  - **View Details:** Expand full information
- **Statistics:**
  - Pending count
  - Confirmed count
  - Total revenue (if pricing implemented)

---

## 5. DATA MODELS & RELATIONSHIPS

### 5.1 Entity Relationship Diagram

```
CustomUser (1) ─── (Many) Property (is owner)
         │
         ├─── (Many) Inquiry (from_user/to_user)
         ├─── (Many) Reservation (from_user/to_user)
         └─── (Many) ContactMessage

Property (1) ─── (Many) PropertyImage
         │
         ├─── (Many) Inquiry
         ├─── (Many) Reservation
         └─── (1) Reservation (deal_confirmed_reservation - nullable)

Inquiry (1) ─── (Many) InquiryMessage
         │
         └─── (1) Property
         └─── (1) CustomUser from_user
         └─── (1) CustomUser to_user
```

### 5.2 Model Specifications

#### CustomUser (accounts/models.py)
**Extends Django's AbstractUser**

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| username | CharField | Unique, required | Login identifier |
| email | EmailField | Unique, required | Communication & login |
| first_name | CharField | Optional | Display name |
| last_name | CharField | Optional | Display name |
| phone | CharField(20) | Optional, blank | Contact number |
| bio | TextField | Optional, blank | User profile description |
| is_banned | BooleanField | Default False | Login access control |
| is_staff | BooleanField | Default False | Admin access control |
| is_active | BooleanField | Default True | Account activation |
| date_joined | DateTimeField | Auto | Registration timestamp |
| last_login | DateTimeField | Auto | Last login timestamp |

**Methods:**
- `get_full_name()` - Returns "First Last" or username if empty

---

#### Property (listings/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| title | CharField(200) | Required, indexed | Property display name |
| slug | SlugField(220) | Unique, auto-generated | SEO URL (handles conflicts) |
| description | TextField | Required | Full property details |
| price | DecimalField(12,2) | Min 0, required | Listing price |
| property_type | CharField | Choices: sale/rent/vacation | Property listing type |
| category | CharField | Choices: apartment/villa/land/commercial | Property classification |
| city | CharField(100) | Required, indexed | Location for filtering |
| address | CharField(255) | Required | Full street address |
| area_sqm | DecimalField(8,2) | Optional, min 0 | Square meters |
| rooms | SmallIntegerField | Optional, min 0 | Number of bedrooms |
| bathrooms | SmallIntegerField | Optional, min 0 | Number of bathrooms |
| floor | SmallIntegerField | Optional | Floor number (0=ground) |
| furnished | BooleanBoolean | Default False | Furnishing status |
| parking | BooleanBoolean | Default False | Parking availability |
| status | CharField | Choices: pending/active/reserved/sold/rented/refused/deleted | Listing status |
| is_featured | BooleanBoolean | Default False | Featured on home page |
| deal_done | BooleanBoolean | Default False | Deal completion flag |
| deal_confirmed_reservation | ForeignKey(Reservation) | Optional, nullable | Confirmed deal reference |
| views_count | IntegerField | Default 0 | Unique visitor count |
| viewed_by | ManyToManyField(User) | Blank | Tracks unique viewers |
| owner | ForeignKey(User) | Required | Property owner |
| search_vector | SearchVectorField | Nullable | PostgreSQL full-text search |
| created_at | DateTimeField | Auto, indexed | Creation timestamp |
| updated_at | DateTimeField | Auto | Last update timestamp |

**Methods:**
- `primary_image` - Returns first image marked as primary
- `is_available` - Returns True if status='active'
- `get_absolute_url()` - Returns detail page URL

**Database Indexes:**
- city, status, property_type, -created_at

---

#### PropertyImage (listings/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| house | ForeignKey(Property) | Required, cascade delete | Parent property |
| image | ImageField | upload_to='properties/' | Image file |
| is_primary | BooleanBoolean | Default False | Featured image flag |
| order | SmallIntegerField | Default 0 | Display order |
| uploaded_at | DateTimeField | Auto | Upload timestamp |

**Validation:**
- Max file size: 10MB
- Allowed types: JPG, PNG, GIF, WebP

---

#### Inquiry (messaging/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| house | ForeignKey(Property) | Required, cascade delete | Inquiry subject |
| from_user | ForeignKey(User) | Required, cascade delete | Inquirer (buyer/renter) |
| to_user | ForeignKey(User) | Required, cascade delete | Property owner |
| message | TextField | Required | Initial inquiry message |
| from_user_read | BooleanBoolean | Default False | Inquirer read replies? |
| to_user_read | BooleanBoolean | Default False | Owner read inquiry? |
| created_at | DateTimeField | Auto, indexed | Creation timestamp |
| updated_at | DateTimeField | Auto | Last update timestamp |

**Validation:**
- from_user ≠ to_user (cannot inquire about own property)
- to_user = property owner (ensures correct recipient)

**Database Indexes:**
- (to_user, -created_at), (to_user, to_user_read), (from_user, from_user_read)

---

#### InquiryMessage (messaging/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| inquiry | ForeignKey(Inquiry) | Required, cascade delete | Parent conversation |
| sender | ForeignKey(User) | Required, cascade delete | Message author |
| message | TextField | Required | Message content |
| is_read | BooleanBoolean | Default False | Message read status |
| created_at | DateTimeField | Auto | Sent timestamp |

**Database Indexes:**
- (inquiry, created_at)

---

#### Reservation (messaging/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| house | ForeignKey(Property) | Required, cascade delete | Property being reserved |
| from_user | ForeignKey(User) | Required, cascade delete | Guest (who reserved) |
| to_user | ForeignKey(User) | Required, cascade delete | Property owner |
| check_in_date | DateField | Optional | Rental start date |
| check_out_date | DateField | Optional | Rental end date |
| message | TextField | Optional, blank | Guest message to owner |
| status | CharField | Choices: pending/confirmed/rejected/cancelled | Reservation state |
| deleted_for_guest_at | DateTimeField | Optional, nullable, indexed | Soft delete timestamp |
| created_at | DateTimeField | Auto, indexed | Creation timestamp |
| updated_at | DateTimeField | Auto | Last update timestamp |

**Validation:**
- from_user ≠ to_user
- to_user = property owner
- check_out_date > check_in_date (if both provided)

**Database Indexes:**
- (house, check_in_date, check_out_date), (to_user, -created_at), (to_user, status)

---

#### ContactMessage (messaging/models.py)

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| name | CharField(100) | Required | Visitor name |
| email | EmailField | Required | Contact email |
| phone | CharField(20) | Optional, blank | Contact phone |
| subject | CharField(200) | Required | Message subject |
| message | TextField | Required | Message body |
| is_read | BooleanBoolean | Default False | Admin read status |
| deleted_at | DateTimeField | Optional, nullable | Soft delete timestamp |
| created_at | DateTimeField | Auto, indexed | Creation timestamp |

---

## 6. USER WORKFLOWS

### 6.1 Buyer/Renter Workflow

```
1. BROWSE
   └─ Anonymous user visits home
   └─ Clicks "Browse Properties"
   └─ Sees paginated property list
   └─ Filters by type, category, city, price
   └─ Searches for specific text (title, description)

2. REVIEW
   └─ Clicks property card
   └─ Views full details & images
   └─ Sees price, features, owner contact
   └─ (View count increments)

3. INQUIRE (if logged in)
   └─ Fills initial inquiry message
   └─ Submits
   └─ Inquiry created with status "pending"
   └─ Owner receives unread notification

4. COMMUNICATE
   └─ Goes to dashboard > inbox
   └─ Sees inquiry conversation
   └─ Replies to owner messages
   └─ Awaits owner response

5. RESERVE (if logged in)
   └─ Selects check-in and check-out dates
   └─ Adds optional message
   └─ Submits reservation
   └─ Reservation status = "pending"
   └─ Owner receives unread notification

6. TRACK
   └─ Views dashboard > reservations
   └─ Sees pending status until owner confirms
   └─ Can delete (soft delete) or cancel
```

### 6.2 Property Owner Workflow

```
1. CREATE
   └─ Login to account
   └─ Go to dashboard > my listings
   └─ Click "Post Property"
   └─ Fill form (title, description, features, images)
   └─ Submit
   └─ Property created with status = "pending"
   └─ Admin reviews and approves

2. WAIT FOR APPROVAL
   └─ Admin must approve (pending → active)
   └─ Or reject (pending → refused)
   └─ Property visible in search only if "active"

3. MANAGE
   └─ Can edit details on own properties
   └─ Can delete (hard deletes cascade)
   └─ Can mark as sold/rented (change status)

4. RECEIVE INQUIRIES
   └─ "You have X unread inquiries" in dashboard
   └─ Click inbox
   └─ Sees inquiries about own properties
   └─ Reads initial inquiry
   └─ Replies with questions/info

5. RECEIVE & MANAGE RESERVATIONS
   └─ Sees pending reservations
   └─ Can confirm (pending → confirmed)
   └─ Can reject (pending → rejected)
   └─ Sees confirmed dates on calendar (future feature)
   └─ Can mark as deal_done when guest arrives

6. COMMUNICATION
   └─ Can message back and forth
   └─ Maintains conversation history
   └─ Sees all inquiries about all own properties
```

### 6.3 Admin Workflow

```
1. LOGIN
   └─ Staff account with is_staff=True
   └─ Access /admin-panel/

2. APPROVE LISTINGS
   └─ Go to listings manager
   └─ Filter by "Pending" status
   └─ Review property details and images
   └─ Click "Approve" → status becomes "active" (searchable)
   └─ Or click "Reject" → status becomes "refused" (hidden)

3. MANAGE USERS
   └─ Go to users manager
   └─ See all registered users
   └─ Ban inappropriate users (is_banned=True)
   └─ Delete spam/test accounts
   └─ Manage staff status (promote/demote)

4. VIEW INQUIRIES/CONTACTS
   └─ See all property inquiries
   └─ View contact form submissions from anonymous users
   └─ Mark as read/respond

5. MANAGE RESERVATIONS
   └─ See all reservations system-wide
   └─ Change status (pending → confirmed/rejected)
   └─ Monitor booking calendar

6. MONITOR PLATFORM
   └─ View dashboard statistics
   └─ See recent activity
   └─ Generate reports (future feature)
```

---

## 7. TECHNICAL ARCHITECTURE

### 7.1 Architecture Pattern
```
Request
   ↓
URL Router (config/urls.py)
   ↓
Views (Class-based views using mixins)
   ↓
Forms/Models (Validation & ORM)
   ↓
Database (PostgreSQL)
   ↓
Response (HTML Template or JSON)
```

### 7.2 App Structure

```
real_estate_project/
├── accounts/               # User authentication
│   ├── models.py          # CustomUser model
│   ├── views.py           # Auth/Profile views
│   ├── forms.py           # Auth forms
│   ├── backends.py        # Email/username auth backend
│   ├── urls.py            # Auth URLs
│   └── templates/         # Auth templates
│
├── listings/              # Property management
│   ├── models.py          # Property, PropertyImage models
│   ├── views.py           # CRUD views for properties
│   ├── forms.py           # PropertyForm, PropertyImageFormSet
│   ├── urls.py            # Listing URLs
│   └── templates/         # Listing templates
│
├── messaging/             # Communication system
│   ├── models.py          # Inquiry, InquiryMessage, Reservation, ContactMessage
│   ├── views.py           # Inquiry/Reservation creation views
│   ├── forms.py           # Message forms
│   ├── urls.py            # Messaging URLs
│   └── templates/         # Messaging templates
│
├── dashboard/             # User dashboard
│   ├── views.py           # Dashboard overview, lists, inbox
│   ├── urls.py            # Dashboard URLs
│   └── templates/         # Dashboard templates
│
├── admin_panel/           # Admin management
│   ├── views.py           # Admin managers (listings, users, contacts)
│   ├── urls.py            # Admin URLs
│   └── templates/         # Admin templates
│
├── core/                  # Shared utilities
│   ├── mixins.py          # OwnerRequiredMixin, StaffRequiredMixin
│   ├── context_processors.py  # Global context data
│   └── apps.py            # App config
│
├── config/                # Django settings
│   ├── base.py            # Base settings (all environments)
│   ├── dev.py             # Development overrides
│   ├── prod.py            # Production overrides
│   ├── settings.py        # Re-exports base.py
│   ├── urls.py            # Root URL router
│   ├── wsgi.py            # WSGI app (production)
│   └── asgi.py            # ASGI app (async)
│
├── templates/             # Global templates
│   ├── base.html          # Base layout with navbar/footer
│   ├── home.html          # Homepage with hero
│   ├── about.html         # About page
│   ├── 404.html           # Error page
│   ├── 500.html           # Error page
│   ├── partials/          # Reusable components
│   ├── accounts/          # Auth templates
│   ├── listings/          # Property templates
│   ├── messaging/         # Message templates
│   ├── dashboard/         # Dashboard templates
│   └── admin_panel/       # Admin templates
│
├── static/                # Static files
│   ├── css/main.css       # Custom Bootstrap overrides + styling
│   ├── js/main.js         # JavaScript utilities
│   └── images/            # Site images
│
├── media/                 # User-uploaded files
│   └── properties/        # Property images
│
├── .env                   # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── manage.py              # Django CLI
└── db.sqlite3             # SQLite database (dev only)
```

### 7.3 Mixins & Permission Patterns

#### OwnerRequiredMixin
```python
class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Checks if current user is the object's owner.
    Returns Http404 if not owner (better UX than 403 Forbidden).
    """
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if obj.owner != self.request.user:
            raise Http404("Not your resource")
        return obj
```

**Used in:**
- PropertyEditView
- PropertyDeleteView

#### StaffRequiredMixin
```python
class StaffRequiredMixin(UserPassesTestMixin):
    """
    Checks if user.is_staff=True and user.is_active=True.
    """
    def test_func(self):
        return self.request.user.is_staff and self.request.user.is_active
```

**Used in:**
- All admin_panel views

### 7.4 View Patterns

#### Pattern 1: List with Filters & Pagination
```python
class PropertyListView(ListView):
    # Handle filtering, sorting, pagination
    # Return filtered queryset
```

#### Pattern 2: Create with Form + Formset
```python
class PropertyCreateView(LoginRequiredMixin, CreateView):
    # Handle property form + image formset
    # Set owner from request.user
    # Save related images
```

#### Pattern 3: Detail with View Tracking
```python
class PropertyDetailView(DetailView):
    # Increment views_count on GET
    # Add to viewed_by ManyToMany
    # Use select_related/prefetch_related for performance
```

#### Pattern 4: Dashboard with Aggregation
```python
def get_dashboard_context(user):
    # Calculate all counters using Count(), Q()
    # Return dict for consistent display across views
```

---

## 8. SECURITY FEATURES

### 8.1 Authentication
- **Custom Backend:** Support login with username OR email
- **Rate Limiting:** 5 login attempts per minute per IP (django-ratelimit)
- **Ban Check:** Banned users cannot login (checked in auth backend)
- **Password Validation:** Min 8 characters (UserAttributeSimilarityValidator removed)
- **Session Security:** CSRF protection on all forms
- **Password Reset:** Token-based via email (1-hour expiry)

### 8.2 Authorization
- **OwnerRequiredMixin:** Verify ownership before allowing edit/delete
- **StaffRequiredMixin:** Verify is_staff before admin panel access
- **LoginRequiredMixin:** Require authentication for protected views
- **404 Strategy:** Return Http404 instead of 403 (don't reveal object existence)

### 8.3 Data Validation
- **Model Clean Methods:** Validate business logic (prevent self-inquiries, etc.)
- **Form Validation:** Validate all user inputs
- **Image Validation:** File type, size, MIME type checks
- **Price Validation:** Minimum 0, decimal precision (12,2)

### 8.4 Data Protection
- **Soft Delete:** Status-based deletion for properties, timestamp for reservations
- **Cascade Handling:** Proper on_delete strategies for foreign keys
- **User Banning:** is_banned flag prevents login while preserving data
- **Privacy:** Users only see own profile, own listings, own inquiries

---

## 9. SEARCH & FILTERING CAPABILITIES

### 9.1 Full-Text Search
- **Database:** PostgreSQL with SearchVector
- **Indexed Fields:**
  - Property title
  - Property description
  - Property city
- **Ranking:** Relevance-ranked results
- **Query:** CharField in form, submitted as GET parameter

### 9.2 Filtering
- **By Property Type:** sale, rent, vacation (dropdown)
- **By Category:** apartment, villa, land, commercial (dropdown)
- **By City:** Text field with autocomplete (from database distinct values)
- **By Price Range:** Min and Max fields with validators
- **By Featured Status:** Checkbox to show featured only
- **By Status:** Hidden filter (only active properties shown to public)

### 9.3 Sorting
- **Latest First:** Default sort by -created_at
- **Price Low to High:** Sort by price ASC
- **Price High to Low:** Sort by price DESC
- **Most Viewed:** Sort by -views_count

---

## 10. ADMIN PANEL FEATURES

### 10.1 Dashboard Statistics
- Total properties (by status)
- Total users
- Total inquiries
- Total reservations
- Pending approvals count
- Recent activity feed

### 10.2 Property Management
- **Approval Workflow:**
  - pending → active (approve) or refused (reject)
- **Preview:** Property details with price, location, image
- **Bulk Actions:** Ready for implementation
- **Status Tracking:** See all properties regardless of visibility

### 10.3 User Management
- **View All Users:** Created date, email, status
- **Ban Users:** Set `is_banned=True` to prevent login
- **Unban Users:** Set `is_banned=False`
- **Delete Users:** Cascade delete user and all related data
- **Staff Management:** Promote regular users to staff (Django admin)
- **Security:** Prevent self-deletion, automatic logout on deletion

### 10.4 Inquiry Management
- **View All Inquiries:** Property, visitor, date, preview
- **Mark as Read:** Toggle read status
- **View Thread:** See all messages in conversation
- **Search:** Find inquiries by property or sender

### 10.5 Contact Management
- **View Contact Forms:** Submissions from anonymous users
- **Mark as Read:** Track which contacts admin saw
- **Delete:** Remove messages
- **Reply:** (Email integration, future enhancement)

---

## 11. FRONTEND FEATURES

### 11.1 Design System
- **Framework:** Bootstrap 5.3.0
- **Custom CSS:** 500+ lines of main.css overrides
- **Variables:** CSS custom properties for colors, spacing
- **Responsive:** Mobile-first design
- **Dark Mode:** (Ready for implementation)

### 11.2 Navigation
- **Header:** Sticky navigation with logo, search, user menu
- **Mobile Drawer:** Hamburger menu for mobile users
- **Footer:** Links, contact info, social media
- **Breadcrumbs:** Navigation clarity on detail pages

### 11.3 Components
- **Cards:** Property showcases with images, price, details
- **Badges:** Status indicators (color-coded)
- **Alerts:** Success, error, warning, info messages
- **Forms:** Styled with Bootstrap, validation feedback
- **Pagination:** Navigation for list pages
- **Modals:** Confirmation dialogs for destructive actions

### 11.4 Interactive Elements
- **Image Gallery:** Lightbox viewer for property photos
- **Formset:** Dynamic form for multiple images
- **Tab Navigation:** Dashboard sections (overview, listings, inbox, reservations)
- **Collapsible:** Inquiry threads expand/collapse
- **Auto-scroll:** Messages scroll to bottom on page load
- **Tooltip:** Help text on form fields

---

## 12. PERFORMANCE & OPTIMIZATION

### 12.1 Database Optimization
- **Indexes:** On frequently queried fields (city, status, created_at)
- **select_related():** Foreign key optimization
- **prefetch_related():** Reverse relation optimization
- **Pagination:** 12-25 items per page (not load all)
- **Atomic Increments:** F() expressions for view_count

### 12.2 Caching (Ready for)
- **Django Cache Framework:** Configured in settings
- **Cache Keys:** Property detail, listing list, user dashboard
- **Invalidation:** On property update/creation
- **TTL:** 1 hour default (configurable)

### 12.3 Query Optimization
```python
# Good ❌ N+1 queries
properties = Property.objects.all()
for prop in properties:
    print(prop.owner.name)  # Extra query per property

# Better ✅ Single query
properties = Property.objects.select_related('owner')

# Best ✅ Reverse relations
properties = Property.objects.prefetch_related('images')
```

---

## 13. FUTURE ENHANCEMENTS

### Phase 2 Features
1. **Payments Integration**
   - Accept reservation down payments
   - Reserve property on payment

2. **Notifications**
   - Email notifications for inquiries
   - SMS notifications for reservations
   - Push notifications (mobile app)

3. **Reviews & Ratings**
   - Rate property
   - Rate owner/agent
   - Display average rating

4. **Advanced Search**
   - Map-based property search
   - Saved searches
   - Search alerts

5. **Analytics Dashboard**
   - Property view reports
   - User demographics
   - Platform statistics

6. **Messaging Enhancements**
   - File attachments
   - Scheduled messages
   - Message templates

7. **Mobile App**
   - Native iOS/Android
   - Push notifications
   - Offline browsing

8. **Compliance**
   - GDPR data export
   - Right to deletion
   - Data privacy policy

---

## 14. API ENDPOINTS SUMMARY

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/` | - | Home page |
| GET | `/listings/` | - | Browse properties |
| GET | `/listings/<slug>/` | - | Property detail |
| GET/POST | `/listings/new/` | ✅ | Create property |
| GET/POST | `/listings/<slug>/edit/` | Owner | Edit property |
| POST | `/listings/<slug>/delete/` | Owner | Delete property |
| POST | `/listings/<slug>/inquiry/` | ✅ | Create inquiry |
| POST | `/listings/<slug>/reserve/` | ✅ | Create reservation |
| POST | `/contact/` | - | Contact form |
| GET/POST | `/accounts/register/` | - | User registration |
| GET/POST | `/accounts/login/` | - | User login |
| POST | `/accounts/logout/` | ✅ | User logout |
| GET/POST | `/accounts/profile/` | ✅ | Edit profile |
| GET/POST | `/accounts/password-reset/` | - | Reset password |
| GET | `/dashboard/` | ✅ | Dashboard overview |
| GET | `/dashboard/listings/` | ✅ | My listings |
| GET | `/dashboard/inbox/` | ✅ | My inbox |
| GET | `/dashboard/reservations/` | ✅ | My reservations |
| POST | `/dashboard/inquiry/<id>/delete/` | ✅ | Delete inquiry |
| GET | `/admin-panel/` | Staff | Admin dashboard |
| GET | `/admin-panel/listings/` | Staff | Manage listings |
| POST | `/admin-panel/listings/<id>/approve/` | Staff | Approve listing |
| POST | `/admin-panel/listings/<id>/reject/` | Staff | Reject listing |
| GET | `/admin-panel/users/` | Staff | Manage users |
| POST | `/admin-panel/users/<id>/ban/` | Staff | Ban user |
| POST | `/admin-panel/users/<id>/delete/` | Staff | Delete user |
| GET | `/admin-panel/contacts/` | Staff | Contact inbox |
| GET | `/admin-panel/reservations/` | Staff | Manage reservations |

---

## 15. TECHNOLOGY STACK

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Django | 4.2 LTS |
| Database | PostgreSQL | 12+ |
| Frontend | Bootstrap | 5.3.0 |
| CSS | Custom + Bootstrap | 500+ lines |
| JavaScript | Vanilla JS | - |
| Forms | Django Forms | - |
| Auth | Django Auth + Custom Backend | - |
| Search | PostgreSQL SearchVector | - |
| Rate Limiting | django-ratelimit | 4.1.0 |
| Image Upload | Django ImageField | - |
| WSGI | Gunicorn | - |
| Web Server | Nginx | - |

---

## 16. DEPLOYMENT CHECKLIST

- [x] Code quality verified
- [x] All migrations applied
- [x] Static files collected
- [x] Environment variables configured
- [x] Database backups automated
- [x] SSL/TLS enabled
- [x] Rate limiting configured
- [x] Logging configured
- [x] Error tracking setup
- [x] Email sending configured
- [x] Password reset emails working
- [x] Admin user created
- [x] Test users created
- [x] Documentation written

---

## 17. SYSTEM REQUIREMENTS

### Minimum
- Python 3.9+
- PostgreSQL 12+
- 2GB RAM
- 10GB storage

### Recommended
- Python 3.11+
- PostgreSQL 15+
- 4GB RAM
- 50GB storage
- Redis for caching
- CDN for media files

---

## 18. CONTACT & SUPPORT

- **Email:** support@propdz.local
- **GitHub Issues:** [@Sabermrddz](https://github.com/Sabermrddz)
- **Documentation:** See inline code comments
- **Q&A:** Team Slack channel

---

**Document Version:** 1.0  
**Last Updated:** March 16, 2026  
**Status:** Complete & Production Ready ✅

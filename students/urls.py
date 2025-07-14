# students/urls.py

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views # Import Django's auth views
from . import views

urlpatterns = [
    # ===================================================================
    # AUTHENTICATION & PASSWORD RESET
    # ===================================================================
    path('login/', views.login_router_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- Password Reset URLs (defined manually to avoid conflicts) ---
    path('password_reset/', 
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', success_url=reverse_lazy('password_reset_done')), 
        name='password_reset'),
    
    path('password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html', success_url=reverse_lazy('password_reset_complete')), 
        name='password_reset_confirm'),

    path('reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
        name='password_reset_complete'),

    # ===================================================================
    # TEACHER PORTAL
    # ===================================================================
    path('', views.dashboard_view, name='dashboard'), 

    # --- Student Management ---
    path('students/', views.StudentListView.as_view(), name='student-list'), 
    path('student/add/', views.StudentCreateView.as_view(), name='student-add'),
    path('student/<int:pk>/', views.StudentDetailView.as_view(), name='student-detail'),
    path('student/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student-edit'),
    path('student/<int:pk>/create-account/', views.create_student_account, name='student-create-account'),
    path('student/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student-delete'),
    path('students/export/csv/', views.export_students_csv, name='export-students-csv'),

    # --- Group Management ---
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('group/add/', views.GroupCreateView.as_view(), name='group-add'),
    path('group/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group-edit'),
    path('group/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group-delete'),
    
    # --- Attendance ---
    path('attendance/', views.attendance_view, name='attendance'),
    
    # --- Assignments & Grading ---
    path('assignments/', views.AssignmentListView.as_view(), name='assignment-list'),
    path('assignment/add/', views.AssignmentCreateView.as_view(), name='assignment-add'),
    path('assignment/<int:pk>/edit/', views.AssignmentUpdateView.as_view(), name='assignment-edit'),
    path('assignment/<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment-delete'),
    path('assignment/<int:pk>/grades/', views.grade_entry_view, name='grade-entry'),
    
    # --- Announcements ---
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement-list'),
    path('announcement/add/', views.AnnouncementCreateView.as_view(), name='announcement-add'),
    path('announcement/<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement-edit'),
    path('announcement/<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement-delete'),

    # ===================================================================
    # STUDENT PORTAL
    # ===================================================================
    path('portal/dashboard/', views.StudentDashboardView.as_view(), name='student-dashboard'),
    path('portal/profile/', views.StudentProfileView.as_view(), name='student-profile'),
    path('portal/assignments/', views.StudentAssignmentsView.as_view(), name='student-assignments'),
    path('portal/assignment/<int:assignment_pk>/submit/', views.AssignmentSubmissionView.as_view(), name='assignment-submit'),
    path('portal/attendance/', views.StudentAttendanceView.as_view(), name='student-attendance'),
]
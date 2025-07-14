# ===================================================================
# 1. IMPORTS
# ===================================================================

# Standard Library Imports
import csv
import random
import string
from datetime import datetime
import json

# Django Core Imports
from django import forms
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
)

# Local Application Imports
from .forms import StudentForm, GroupForm ,SubmissionForm
from .models import Student, Group, Attendance, Assignment, Grade ,Announcement



# ===================================================================
# 2. MIXINS & AUTHENTICATION
# ===================================================================

class AuthRequiredMixin(LoginRequiredMixin):
    """Ensures user is logged in for teacher-specific views."""
    login_url = '/login/'

class StudentRequiredMixin(LoginRequiredMixin):
    """Ensures user is a logged-in student and not a teacher."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_superuser:
            messages.warning(request, "This page is for students only.")
            return redirect('dashboard') 
        
        try:
            self.student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            logout(request)
            messages.error(request, "Your student profile could not be found. Please contact your teacher.")
            return redirect('login')

        return super().dispatch(request, *args, **kwargs)
    
def login_router_view(request):
    """Redirects user to the appropriate dashboard after login."""
    if request.user.is_authenticated:
        return redirect('dashboard' if request.user.is_superuser else 'student-dashboard')
    
    class CustomLoginView(BaseLoginView):
        template_name = 'students/login.html'
    
    return CustomLoginView.as_view()(request)


# ===================================================================
# 3. TEACHER PORTAL VIEWS
# ===================================================================

# --- Dashboard ---
@login_required
def dashboard_view(request):
    """Displays the main dashboard for teachers."""
    if not request.user.is_superuser:
        return redirect('student-dashboard')
        
    today = timezone.now().date()

    # --- Data Gathering ---
    total_students = Student.objects.count()
    total_groups = Group.objects.count()
    todays_attendance = Attendance.objects.filter(date=today)
    students_marked_today = todays_attendance.values_list('student_id', flat=True)
    attendance_stats = Attendance.objects.values('status').annotate(count=Count('status')).order_by('status')

    # --- Assemble the complete context dictionary ---
    context = {
        'total_students': total_students,
        'total_groups': total_groups,
        'present_count': todays_attendance.filter(status='Present').count(),
        'absent_count': todays_attendance.filter(status='Absent').count(),
        'unmarked_count': total_students - len(students_marked_today),
        'recently_added_students': Student.objects.order_by('-id')[:5],
        'students_missing_info': Student.objects.filter(
            Q(phone__isnull=True) | Q(phone__exact='') | 
            Q(email__isnull=True) | Q(email__exact='')
        ).order_by('full_name'),
        'today': today,
        'chart_labels': [item['status'] for item in attendance_stats],
        'chart_data': [item['count'] for item in attendance_stats],
    }
    
    return render(request, 'students/dashboard.html', context)


# --- Student Management ---
class StudentListView(AuthRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('group').order_by('full_name')
        query = self.request.GET.get('q')
        group_id = self.request.GET.get('group')

        if query:
            queryset = queryset.filter(Q(full_name__icontains=query) | Q(email__icontains=query) | Q(telegram__icontains=query))
        if group_id:
            queryset = queryset.filter(group__id=group_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all().order_by('name')
        context['selected_group'] = self.request.GET.get('group', '')
        return context

class StudentDetailView(AuthRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

class StudentCreateView(AuthRequiredMixin, SuccessMessageMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-list')
    success_message = "Student '%(full_name)s' was created successfully."

class StudentUpdateView(AuthRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-list')
    success_message = "Student '%(full_name)s' was updated successfully."

class StudentDeleteView(AuthRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student-list')
    success_message = "Student was deleted successfully."
    
    # This is needed for SuccessMessageMixin to work on a DeleteView
    def get_success_message(self, cleaned_data):
        return self.success_message


# --- Group Management ---
class GroupListView(AuthRequiredMixin, ListView):
    model = Group
    template_name = 'students/group_list.html'
    context_object_name = 'groups'
    queryset = Group.objects.all().order_by('name')

class GroupCreateView(AuthRequiredMixin, SuccessMessageMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'students/group_form.html'
    success_url = reverse_lazy('group-list')
    success_message = "Group '%(name)s' was created successfully."

class GroupUpdateView(AuthRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'students/group_form.html'
    success_url = reverse_lazy('group-list')
    success_message = "Group '%(name)s' was updated successfully."

class GroupDeleteView(AuthRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Group
    template_name = 'students/group_confirm_delete.html'
    success_url = reverse_lazy('group-list')
    success_message = "Group was deleted successfully."
    
    def get_success_message(self, cleaned_data):
        return self.success_message

# --- Attendance Management ---
@login_required
def attendance_view(request):
    date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    if request.method == 'POST':
        for student in Student.objects.all():
            if status := request.POST.get(f'status_{student.id}'):
                Attendance.objects.update_or_create(student=student, date=selected_date, defaults={'status': status})
        messages.success(request, f"Attendance for {selected_date.strftime('%B %d, %Y')} saved successfully.")
        return redirect(f"{request.path}?date={selected_date.strftime('%Y-%m-%d')}")

    context = {
        'students': Student.objects.all().order_by('group__name', 'full_name'),
        'attendance_records': {rec.student_id: rec.status for rec in Attendance.objects.filter(date=selected_date)},
        'selected_date': selected_date,
        'status_choices': Attendance.STATUS_CHOICES,
    }
    return render(request, 'students/attendance_form.html', context)


# --- Assignment & Grading Management ---
class AssignmentListView(AuthRequiredMixin, ListView):
    model = Assignment
    template_name = 'students/assignment_list.html'
    context_object_name = 'assignments'

class AssignmentCreateView(AuthRequiredMixin, SuccessMessageMixin, CreateView):
    model = Assignment
    fields = ['title', 'group', 'description', 'file', 'due_date'] 
    template_name = 'students/assignment_form.html'
    success_url = reverse_lazy('assignment-list')
    success_message = "Assignment '%(title)s' was created successfully."
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['due_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['group'].widget.attrs.update({'class': 'form-select'})
        form.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        form.fields['file'].widget.attrs.update({'class': 'form-control'})
        return form

class AssignmentUpdateView(AuthRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Assignment
    fields = ['title', 'group', 'description', 'file', 'due_date']
    template_name = 'students/assignment_form.html'
    success_url = reverse_lazy('assignment-list')
    success_message = "Assignment '%(title)s' was updated successfully."
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['due_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['group'].widget.attrs.update({'class': 'form-select'})
        form.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        form.fields['file'].widget.attrs.update({'class': 'form-control'})
        return form

class AssignmentDeleteView(AuthRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Assignment
    template_name = 'students/assignment_confirm_delete.html'
    success_url = reverse_lazy('assignment-list')
    success_message = "Assignment was deleted successfully."

    def get_success_message(self, cleaned_data):
        return self.success_message

@login_required
def grade_entry_view(request, pk):
    assignment = Assignment.objects.get(pk=pk)
    if request.method == 'POST':
        for student in Student.objects.filter(group=assignment.group):
            if score := request.POST.get(f'score_{student.id}'):
                comment = request.POST.get(f'comment_{student.id}', '')
                Grade.objects.update_or_create(student=student, assignment=assignment, defaults={'score': score, 'comment': comment})
        messages.success(request, f"Grades for '{assignment.title}' saved.")
        return redirect('assignment-list')

    context = {
        'assignment': assignment,
        'students': Student.objects.filter(group=assignment.group).order_by('full_name'),
        'grades': {grade.student_id: grade for grade in Grade.objects.filter(assignment=assignment)},
    }
    return render(request, 'students/grade_entry_form.html', context)


# --- Utility Views ---
@login_required
def create_student_account(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    student = Student.objects.get(pk=pk)
    if student.user:
        messages.warning(request, f"Student {student.full_name} already has an account.")
        return redirect('student-detail', pk=pk)

    username = f"{student.full_name.split(' ')[0].lower().replace(' ', '')}{student.id}"
    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    user = User.objects.create_user(username=username, password=password)
    student.user = user
    student.save()
    
    messages.success(request, f"Account created for {student.full_name}. Username: {username}, Password: {password}")
    return redirect('student-detail', pk=pk)

@login_required
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Group', 'Phone', 'Email', 'Telegram', 'Note'])

    for student in Student.objects.all().select_related('group').order_by('group__name', 'full_name'):
        writer.writerow([student.full_name, student.group.name, student.phone, student.email, student.telegram, student.note])
    
    return response


# ===================================================================
# 4. STUDENT PORTAL VIEWS
# ===================================================================

# students/views.py

class StudentDashboardView(StudentRequiredMixin, TemplateView):
    template_name = 'students/portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.student
        
        # --- Assignment & Grade Logic ---
        assignments = Assignment.objects.filter(group=student.group)
        
        graded_assignments_with_scores = Grade.objects.filter(
            student=student, 
            score__isnull=False
        ).select_related('assignment').order_by('assignment__due_date', 'assignment__created_at')
        
        graded_assignment_ids = [grade.assignment.id for grade in graded_assignments_with_scores]
        
        context['completed_assignments'] = assignments.filter(id__in=graded_assignment_ids)
        pending_and_overdue = assignments.exclude(id__in=graded_assignment_ids)
        context['pending_assignments'] = pending_and_overdue.filter(Q(due_date__gte=timezone.now().date()) | Q(due_date__isnull=True))
        context['overdue_assignments'] = pending_and_overdue.filter(due_date__lt=timezone.now().date())
        
        # --- Chart Data ---
        # Pass the queryset itself to the template
        context['graded_assignments_for_chart'] = graded_assignments_with_scores

        # --- Other context data ---
        context['student'] = student
        context['announcements'] = Announcement.objects.filter(
            Q(group=student.group) | Q(group__isnull=True)
        )[:5]
        
        return context

class StudentProfileView(StudentRequiredMixin, UpdateView):
    model = Student
    fields = ['photo', 'phone', 'email', 'telegram']
    template_name = 'students/portal/profile.html'
    success_url = reverse_lazy('student-dashboard')
    
    def get_object(self, queryset=None):
        return self.student
    
    def get_form(self, form_class=None):
        # +++ ADD THIS METHOD TO STYLE THE FORM +++
        form = super().get_form(form_class)
        form.fields['photo'].widget.attrs.update({'class': 'form-control'})
        form.fields['phone'].widget.attrs.update({'class': 'form-control'})
        form.fields['email'].widget.attrs.update({'class': 'form-control'})
        form.fields['telegram'].widget.attrs.update({'class': 'form-control'})
        return form
    
    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)

class StudentAssignmentsView(StudentRequiredMixin, TemplateView):
    template_name = 'students/portal/assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.student
        
        assignments = Assignment.objects.filter(group=student.group)
        grades = Grade.objects.filter(student=student).select_related('assignment')
        graded_assignment_ids = grades.values_list('assignment_id', flat=True)

        context['student'] = student
        context['grades'] = grades
        context['pending_assignments'] = assignments.exclude(id__in=graded_assignment_ids)
        context['graded_assignment_ids'] = graded_assignment_ids # Pass this for the template logic
        context['today'] = timezone.now().date() # Pass today's date
        return context
    
class StudentAttendanceView(StudentRequiredMixin, TemplateView):
    template_name = 'students/portal/attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.student
        
        # Get all attendance records for this student
        context['attendance_records'] = Attendance.objects.filter(student=student).order_by('-date')
        context['student'] = student
        return context
    
class AssignmentSubmissionView(StudentRequiredMixin, UpdateView):
    model = Grade
    form_class = SubmissionForm
    template_name = 'students/portal/submission_form.html'
    
    def get_object(self, queryset=None):
        # Get or create a Grade object for this student and assignment
        assignment_pk = self.kwargs.get('assignment_pk')
        assignment = Assignment.objects.get(pk=assignment_pk)
        
        # Ensure the student is in the correct group for this assignment
        if self.student.group != assignment.group:
            from django.http import Http404
            raise Http404("Assignment not found for your group.")

        obj, created = Grade.objects.get_or_create(
            student=self.student,
            assignment=assignment,
        )
        return obj

    def form_valid(self, form):
        grade = form.save(commit=False)
        grade.submitted_at = timezone.now() # Mark submission time
        grade.save()
        messages.success(self.request, f"Your submission for '{grade.assignment.title}' was uploaded successfully.")
        return redirect('student-assignments')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.object.assignment
        return context
    

# ===================================================================
# 5. ANNOUNCEMENT MANAGEMENT
# ===================================================================
class AnnouncementListView(AuthRequiredMixin, ListView):
    model = Announcement
    template_name = 'students/teacher/announcement_list.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        # Teachers only see their own announcements
        return Announcement.objects.filter(author=self.request.user)

class AnnouncementCreateView(AuthRequiredMixin, SuccessMessageMixin, CreateView):
    model = Announcement
    fields = ['title', 'content', 'group']
    template_name = 'students/teacher/announcement_form.html'
    success_url = reverse_lazy('announcement-list')
    success_message = "Announcement created successfully."

    def form_valid(self, form):
        # Automatically set the author to the logged-in teacher
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['content'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        form.fields['group'].widget.attrs.update({'class': 'form-select'})
        return form

class AnnouncementUpdateView(AuthRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Announcement
    fields = ['title', 'content', 'group']
    template_name = 'students/teacher/announcement_form.html'
    success_url = reverse_lazy('announcement-list')
    success_message = "Announcement updated successfully."
    
    def get_queryset(self):
        return Announcement.objects.filter(author=self.request.user)

class AnnouncementDeleteView(AuthRequiredMixin, DeleteView):
    model = Announcement
    template_name = 'students/teacher/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcement-list')

    def get_queryset(self):
        return Announcement.objects.filter(author=self.request.user)
# students/models.py

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # We will create this URL later
        return reverse('course-detail', kwargs={'pk': self.pk})

class Enrollment(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A student can only be enrolled in a course once
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.full_name} enrolled in {self.course.title}"
    
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Group Name")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group-list')

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True, default='student_photos/default.png')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="students", verbose_name="Group")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telegram = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram")
    note = models.TextField(blank=True, null=True, verbose_name="Note")

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('student-list')


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    class Meta:
        # A student can only have one status per day
        unique_together = ('student', 'date')
        ordering = ['-date', 'student__full_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"
    
# students/models.py
# Add these new models at the end of the file

# students/models.py

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='assignments')
    description = models.TextField(blank=True, null=True) 
    file = models.FileField(upload_to='assignments/', blank=True, null=True) 
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.group.name})"
    
    class Meta:
        ordering = ['-due_date']

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    submission_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'assignment') # A student gets one grade per assignment
    
    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}: {self.score}"
    

class Announcement(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    # If group is null, the announcement is for ALL students.
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, 
                              help_text="Leave blank to send to all students.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


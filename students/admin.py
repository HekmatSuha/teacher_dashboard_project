# students/admin.py

from django.contrib import admin
from .models import (
    Student,
    Group,
    Assignment,
    Grade,
    Attendance,
    Course,
    Enrollment,
    Announcement,
)

# Simple registration
admin.site.register(Student)
admin.site.register(Group)
admin.site.register(Assignment)
admin.site.register(Grade)
admin.site.register(Attendance)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Announcement)
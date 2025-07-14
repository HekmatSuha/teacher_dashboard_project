# students/admin.py

from django.contrib import admin
from .models import Student, Group, Assignment, Grade, Attendance

# Simple registration
admin.site.register(Student)
admin.site.register(Group)
admin.site.register(Assignment)
admin.site.register(Grade)
admin.site.register(Attendance)
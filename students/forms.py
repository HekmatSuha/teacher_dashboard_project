# students/forms.py

from django import forms
from .models import Student, Group, Grade, Course


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'group','photo', 'phone', 'email', 'telegram', 'note']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Grade
        # +++ ADD 'submission_text' TO THE FIELDS LIST +++
        fields = ['submission_file', 'submission_text']
        widgets = {
            'submission_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            # +++ ADD A WIDGET FOR THE TEXT AREA +++
            'submission_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Type your response here...'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
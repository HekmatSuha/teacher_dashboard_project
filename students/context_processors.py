# students/context_processors.py

from .models import Student

def student_profile_picture(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            student = Student.objects.get(user=request.user)
            return {'student_photo_url': student.photo.url}
        except Student.DoesNotExist:
            return {}
    return {}
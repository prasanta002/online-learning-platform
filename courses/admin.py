from django.contrib import admin

from .models import (
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Certificate,
    Payment,
)


admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Lesson)
admin.site.register(LessonProgress)
admin.site.register(Certificate)
admin.site.register(Payment)
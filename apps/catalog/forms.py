from django import forms

from .models import Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "subject",
            "headline",
            "overview",
            "thumbnail",
            "pricing_model",
            "price",
        ]
        widgets = {
            "overview": forms.Textarea(attrs={"rows": 5}),
        }

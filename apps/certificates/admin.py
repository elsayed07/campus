from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["serial", "enrollment", "issued_at"]
    search_fields = ["serial", "enrollment__student__email", "enrollment__course__title"]
    readonly_fields = ["serial", "issued_at", "pdf"]

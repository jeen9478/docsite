
# Register your models here.
from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_no', 'subject', 'sender', 'is_accepted', 'created_at')
    list_filter = ('is_accepted',)

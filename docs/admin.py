from django.contrib import admin
from .models import Document, Signature, DocumentRoute, DocumentFlow, Department, Profile


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_no', 'subject', 'sender', 'is_accepted', 'status', 'created_at')
    list_filter = ('is_accepted', 'status')


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ('document', 'signer', 'signed_at', 'page_number')
    list_filter = ('signed_at',)
    readonly_fields = ('signed_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'role')
    list_filter = ('role', 'department')
    list_editable = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(DocumentRoute)
class DocumentRouteAdmin(admin.ModelAdmin):
    list_display = ('document', 'department', 'received', 'received_at')
    list_filter = ('received',)


@admin.register(DocumentFlow)
class DocumentFlowAdmin(admin.ModelAdmin):
    list_display = ('document', 'from_department', 'to_department', 'sent_by', 'sent_at')

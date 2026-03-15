import os
import base64
from io import BytesIO
from urllib import request
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from .models import Document, Signature, DocumentRoute, DocumentFlow, Notification, Department, Profile
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings
from .decorators import role_required
from PIL import Image
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import DocumentForm, UserCreateForm, UserUpdateForm
from django.shortcuts import redirect

@login_required
def document_list(request):
    documents = Document.objects.all()
    return render(request, 'document_list.html', {
        'documents': documents
    })

def view_file(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    response = FileResponse(doc.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{doc.file.name}"'
    return response

@login_required
def inbox(request):
    my_dept = request.user.profile.department

    routes = DocumentRoute.objects.filter(
        department=my_dept
    ).select_related('document')

    return render(request, 'inbox.html', {
        'routes': routes
    })


@login_required
@require_POST
def send_to_director(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    doc.status = 'waiting'
    doc.save()

    # แจ้งเตือนผู้บริหารทุกคน
    executives = User.objects.filter(profile__role__in=['director', 'admin'])
    for exec_user in executives:
        Notification.objects.create(
            user=exec_user,
            message=f'มีเอกสาร {doc.doc_no} รอพิจารณา'
        )

    return redirect('detail', pk=doc.pk)

@login_required
@require_POST
def sign_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    signature_data = request.POST.get("signature_data")
    pos_x = float(request.POST.get("pos_x", 100))
    pos_y = float(request.POST.get("pos_y", 100))
    page_number = int(request.POST.get("page_number", 0))

    sig_width = float(request.POST.get("sig_width", 150))
    sig_height = float(request.POST.get("sig_height", 80))

    if not signature_data or not signature_data.startswith("data:image/"):
        return redirect("detail", pk=doc.pk)

    # ===== แปลง base64 =====
    format_str, imgstr = signature_data.split(";base64,")
    ext = format_str.split("/")[-1]
    filename = f"signature_{doc.doc_no}_{request.user.username}.{ext}"
    image_file = ContentFile(base64.b64decode(imgstr), name=filename)

    # ===== บันทึก Signature model =====
    sig, created = Signature.objects.get_or_create(
        document=doc,
        signer=request.user,
        defaults={
            "comment": request.POST.get("comment", ""),
            "pos_x": pos_x,
            "pos_y": pos_y,
            "page_number": page_number,
        }
    )

    if not created:
        sig.comment = request.POST.get("comment", "")
        sig.pos_x = pos_x
        sig.pos_y = pos_y
        sig.page_number = page_number

    sig.signature_image.save(filename, image_file, save=True)

    # ===== ฝังลง PDF =====
    pdf_reader = PdfReader(doc.file.path)
    writer = PdfWriter()

    page = pdf_reader.pages[page_number]
    page_width = float(page.mediabox.width)
    page_height = float(page.mediabox.height)

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    can.drawImage(
        sig.signature_image.path,
        sig.pos_x,
        sig.pos_y,
        width=sig_width,
        height=sig_height,
        mask='auto'
    )

    can.save()
    packet.seek(0)

    overlay_pdf = PdfReader(packet)

    for i in range(len(pdf_reader.pages)):
        original_page = pdf_reader.pages[i]
        if i == page_number:
            original_page.merge_page(overlay_pdf.pages[0])
        writer.add_page(original_page)




    signed_filename = f"signed_{doc.pk}.pdf"
    signed_path = os.path.join(settings.MEDIA_ROOT, "uploads", signed_filename)

    with open(signed_path, "wb") as f:
        writer.write(f)

    doc.file.name = f"uploads/{signed_filename}"
    doc.status = "signed"
    doc.is_accepted = True
    doc.save()

    # ===== Notification =====
    if doc.created_by:
        Notification.objects.create(
            user=doc.created_by,
            message=f"เอกสาร {doc.doc_no} ผอ.ลงนามแล้ว"
        )

    return redirect("detail", pk=doc.pk)

@login_required
@require_POST
def forward_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    to_dept = request.POST['department']

    DocumentFlow.objects.create(
        document=doc,
        from_department=doc.department,
        to_department=to_dept,
        sent_by=request.user,
        comment=request.POST.get('comment', '')
    )

    DocumentRoute.objects.create(
        document=doc,
        department=to_dept
    )

    doc.status = 'forwarded'
    doc.save()

    # แจ้งคนในแผนกปลายทาง
    users = User.objects.filter(profile__department=to_dept)
    for u in users:
        Notification.objects.create(
            user=u,
            message=f'มีเอกสารเข้าใหม่ {doc.doc_no}'
        )

    return redirect('detail', pk=doc.doc_no)


@login_required
@require_POST
def receive_document(request, route_id):
    route = get_object_or_404(DocumentRoute, id=route_id)
    route.received = True
    route.received_at = timezone.now()
    route.save()
    return redirect('dept_inbox')


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    departments = Department.objects.all()
    signatures = doc.signatures.select_related('signer').all()
    user_has_signed = doc.signatures.filter(signer=request.user).exists()
    can_sign = doc.status in ('waiting', 'signed') and not user_has_signed
    return render(request, 'document_detail.html', {
        'doc': doc,
        'departments': departments,
        'signatures': signatures,
        'can_sign': can_sign,
    })


@login_required
def document_add(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.created_by = request.user
            doc.save()

            # แจ้งเตือนทุกคน (ยกเว้นผู้สร้าง) ว่ามีเอกสารใหม่เข้ามา
            other_users = User.objects.exclude(pk=request.user.pk)
            for u in other_users:
                Notification.objects.create(
                    user=u,
                    message=f'มีเอกสารใหม่ {doc.doc_no} - {doc.subject}'
                )

            return redirect('inbox_dashboard')
    else:
        form = DocumentForm()

    return render(request, 'document_add.html', {'form': form})


@login_required
@role_required(['admin', 'director'])
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.delete()
    return redirect('document_list')


@login_required
@role_required(['admin', 'director'])
def document_edit(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            return redirect('detail', pk=doc.pk)
    else:
        form = DocumentForm(instance=doc)

    return render(request, 'document_edit.html', {
        'form': form,
        'doc': doc,
    })

@login_required
def document_list(request):
    q = request.GET.get('q', '')
    department = request.GET.get('department', '')
    secret = request.GET.get('secret', '')
    urgency = request.GET.get('urgency', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    documents = Document.objects.all().order_by('-created_at')

    if q:
        documents = documents.filter(
            Q(doc_no__icontains=q) |
            Q(subject__icontains=q) |
            Q(sender__icontains=q)
        )

    if department:
        documents = documents.filter(department=department)

    if secret:
        documents = documents.filter(secret_level=secret)

    if urgency:
        documents = documents.filter(urgency=urgency)

    if date_from:
        documents = documents.filter(date__gte=date_from)

    if date_to:
        documents = documents.filter(date__lte=date_to)

    departments = Document.objects.values_list('department', flat=True).distinct()

    return render(request, 'document_list.html', {
        'documents': documents,
        'q': q,
        'department': department,
        'secret': secret,
        'urgency': urgency,
        'date_from': date_from,
        'date_to': date_to,
        'departments': departments,
    })

@login_required
def download_file(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    if not doc.file:
        raise Http404("ไม่พบไฟล์")

    file_path = doc.file.path
    file_name = os.path.basename(file_path)

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=file_name
    )


@login_required
def inbox_dashboard(request):
    documents = Document.objects.all().order_by('-created_at')

    total_docs = documents.count()
    accepted_docs = documents.filter(is_accepted=True).count()
    pending_docs = documents.filter(is_accepted=False).count()

    # การแจ้งเตือนของผู้ใช้ปัจจุบัน
    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')

    context = {
        'documents': documents,
        'total_docs': total_docs,
        'accepted_docs': accepted_docs,
        'pending_docs': pending_docs,
        'notifications': notifications,
    }
    return render(request, 'inbox_dashboard.html', context)


@login_required
@role_required('director', 'admin')
def director_dashboard(request):
    waiting_docs = Document.objects.filter(status='waiting').order_by('-created_at')
    signed_docs = Document.objects.filter(status='signed').order_by('-created_at')

    context = {
        'waiting_docs': waiting_docs,
        'signed_docs': signed_docs,
    }
    return render(request, 'director_dashboard.html', context)


@login_required
@require_POST
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('inbox_dashboard')

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"


class UserCreateView(LoginRequiredMixin, CreateView):

    model = User
    form_class = UserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):

        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        role = form.cleaned_data['role']
        department = form.cleaned_data['department']

        profile, created = Profile.objects.get_or_create(user=user)

        profile.role = role
        profile.department = department
        profile.save()
        
        return redirect('user_list')


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    form_class = UserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):

        user = form.save(commit=False)

        if form.cleaned_data['password']:
            user.set_password(form.cleaned_data['password'])

        user.save()

        user.profile.role = form.cleaned_data['role']
        user.profile.department = form.cleaned_data['department']
        user.profile.save()

        return redirect(self.success_url)


class UserDeleteView(LoginRequiredMixin, DeleteView):

    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):

        user = self.get_object()

        # Director ห้ามลบ Admin
        if request.user.profile.role == "director" and user.profile.role == "admin":
            from django.http import HttpResponse
            return HttpResponse("Director cannot delete Admin")

        return super().dispatch(request, *args, **kwargs)

def user_create(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']
        department_id = request.POST['department']

        user = User.objects.create_user(
            username=username,
            password=password
        )

        department = Department.objects.get(id=department_id)

        Profile.objects.create(
            user=user,
            role=role,
            department=department
        )

        return redirect('user_list')
import os
import base64
from io import BytesIO
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from .forms import DocumentForm
from .models import Document, Signature, DocumentRoute, DocumentFlow, Notification, Department
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings

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
def send_to_director(request, doc_no):
    doc = get_object_or_404(Document, doc_no=doc_no)

    doc.status = 'waiting'
    doc.save()

    # แจ้งเตือนผอ. (ถ้ามี user ชื่อ director)
    try:
        director = User.objects.get(username='director')
        Notification.objects.create(
            user=director,
            message=f'มีเอกสาร {doc.doc_no} รอพิจารณา'
        )
    except User.DoesNotExist:
        pass

    return redirect('detail', pk=doc.doc_no)


@login_required
@require_POST
def sign_document(request, doc_no):
    doc = get_object_or_404(Document, doc_no=doc_no)

    signature_data = request.POST.get("signature_data")
    pos_x = float(request.POST.get("pos_x", 100))
    pos_y = float(request.POST.get("pos_y", 100))
    page_number = int(request.POST.get("page_number", 0))

    if not signature_data or not signature_data.startswith("data:image/"):
        return redirect("detail", pk=doc.doc_no)

    # ===== แปลง base64 =====
    format_str, imgstr = signature_data.split(";base64,")
    ext = format_str.split("/")[-1]
    filename = f"signature_{doc.doc_no}_{request.user.username}.{ext}"
    image_file = ContentFile(base64.b64decode(imgstr), name=filename)

    # ===== บันทึก Signature model =====
    sig, created = Signature.objects.get_or_create(
        document=doc,
        defaults={
            "signer": request.user,
            "comment": request.POST.get("comment", "")
        }
    )

    sig.signature_image.save(filename, image_file, save=True)

    # ===== ฝังลง PDF =====
    pdf_reader = PdfReader(doc.file.path)
    writer = PdfWriter()

    packet = BytesIO()
    can = canvas.Canvas(packet)

    page = pdf_reader.pages[page_number]
    page_height = float(page.mediabox.height)

    image = ImageReader(sig.signature_image.path)

    can.drawImage(
        image,
        pos_x,
        page_height - pos_y - 80,
        width=150,
        height=80,
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

    signed_filename = f"signed_{doc.doc_no}.pdf"
    signed_path = os.path.join(settings.MEDIA_ROOT, "uploads", signed_filename)

    with open(signed_path, "wb") as f:
        writer.write(f)

    doc.file.name = f"uploads/{signed_filename}"
    doc.status = "signed"
    doc.save()

    # ===== Notification =====
    if doc.created_by:
        Notification.objects.create(
            user=doc.created_by,
            message=f"เอกสาร {doc.doc_no} ผอ.ลงนามแล้ว"
        )

    return redirect("detail", pk=doc.doc_no)



@login_required
@require_POST
def forward_document(request, doc_no):
    doc = get_object_or_404(Document, doc_no=doc_no)
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
    return render(request, 'document_detail.html', {
        'doc': doc,
        'departments': departments,
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
@require_POST
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.delete()
    return redirect('document_list')


@login_required
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
def doc_list(request):
    q = request.GET.get('q', '')
    department = request.GET.get('department', '')
    secret = request.GET.get('secret', '')
    urgency = request.GET.get('urgency', '')

    docs = Document.objects.all()

    if q:
        docs = docs.filter(
            Q(doc_no__icontains=q) |
            Q(subject__icontains=q)
        )

    if department:
        docs = docs.filter(department=department)

    if secret:
        docs = docs.filter(secret_level=secret)

    if urgency:
        docs = docs.filter(urgency=urgency)

    departments = Document.objects.values_list(
        'department', flat=True
    ).distinct()

    context = {
        'docs': docs,
        'q': q,
        'department': department,
        'secret': secret,
        'urgency': urgency,
        'departments': departments
    }
    return render(request, 'doc_list.html', context)


@login_required
def download_file(request, doc_no):
    doc = get_object_or_404(Document, doc_no=doc_no)

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

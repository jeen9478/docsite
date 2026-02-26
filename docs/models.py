from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Document(models.Model):

    TYPE_CHOICES = [
        ('internal','ภายใน'),
        ('external','ภายนอก')
    ]

    SECRET_CHOICES = [
        ('normal','ปกติ'),
        ('secret','ลับ'),
        ('verysecret','ลับมาก'),
        ('topsecret','ลับที่สุด')
    ]

    URGENCY_CHOICES = [
        ('normal','ปกติ'),
        ('urgent','ด่วน'),
        ('veryurgent','ด่วนมาก'),
        ('topurgent','ด่วนที่สุด')
    ]

    STATUS_CHOICES = [
        ('draft','ร่าง'),
        ('waiting','รอผอ.พิจารณา'),
        ('signed','ผอ.ลงนามแล้ว'),
        ('forwarded','ส่งต่อแผนกแล้ว'),
    ]
    
    id = models.BigAutoField(primary_key=True)

    doc_no = models.CharField(
        max_length=50,
        unique=True
    )

    date = models.DateField()
    from_org = models.CharField(max_length=255, blank=True)
    to_org = models.CharField(max_length=255, blank=True)
    officer = models.CharField(max_length=100, blank=True)
    sender = models.CharField(max_length=255, blank=True)  # ผู้ส่ง
    is_accepted = models.BooleanField(default=False)  # สถานะตอบรับ
    subject = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    doc_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='internal')
    secret_level = models.CharField(max_length=12, choices=SECRET_CHOICES, default='normal')
    urgency = models.CharField(max_length=12, choices=URGENCY_CHOICES, default='normal')
    remark = models.TextField(blank=True)
    file = models.FileField(upload_to='uploads/', validators=[FileExtensionValidator(['pdf'])], blank=False, null=True)

    #  เพิ่มเพื่อ workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

class Signature(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    signer = models.ForeignKey(User, on_delete=models.CASCADE)
    signature_image = models.ImageField(upload_to='signatures/')
    signed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    pos_x = models.FloatField(default=100)
    pos_y = models.FloatField(default=100)
    page_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ['document', 'signer']

    def __str__(self):
        return f'ลายเซ็น {self.signer.username} - {self.document.doc_no}'

class DocumentRoute(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    received = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.document.doc_no} → {self.department}'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class DocumentFlow(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='flows'
    )

    from_department = models.CharField(
        max_length=100,
        blank=True
    )
    to_department = models.CharField(
        max_length=100
    )

    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    comment = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.doc_no} → {self.to_department}"
  
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'ผู้ดูแลระบบ'),
        ('doctor', 'แพทย์'),
        ('nurse', 'พยาบาล/เจ้าหน้าที่'),
        ('executive', 'ผู้บริหาร'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='nurse',
        verbose_name='บทบาท'
    )

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
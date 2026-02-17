from django import forms   # ✅ เพิ่มบรรทัดนี้
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'doc_no',
            'date',
            'subject',
            'sender',
            'from_org',
            'to_org',
            'department',
            'doc_type',
            'secret_level',
            'urgency',
            'officer',
            'remark',
            'file',
        ]

        labels = {
            'doc_no': 'เลขที่หนังสือรับ',
            'date': 'วันที่รับหนังสือ',
            'subject': 'เรื่อง',
            'sender': 'ผู้ส่ง',
            'from_org': 'จากหน่วยงาน',
            'to_org': 'ถึงหน่วยงาน',
            'department': 'แผนก / ฝ่าย',
            'doc_type': 'ประเภทหนังสือ',
            'secret_level': 'ชั้นความลับ',
            'urgency': 'ระดับความด่วน',
            'officer': 'เจ้าหน้าที่รับเรื่อง',
            'remark': 'หมายเหตุ',
            'file': 'แนบไฟล์เอกสาร',
        }

        widgets = {
            'doc_no': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'sender': forms.TextInput(attrs={'class': 'form-control'}),
            'from_org': forms.TextInput(attrs={'class': 'form-control'}),
            'to_org': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'secret_level': forms.Select(attrs={'class': 'form-select'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'officer': forms.TextInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }



from django import forms   # ✅ เพิ่มบรรทัดนี้
from .models import Document
from django.contrib.auth.models import User
from .models import Profile, Department

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
            'department': forms.Select(attrs={'class': 'form-select'}),
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

class UserCreateForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)

    department = forms.ModelChoiceField(
        queryset=Profile._meta.get_field('department').related_model.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

class UserUpdateForm(forms.ModelForm):

    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        label="บทบาท"
    )

    department = forms.CharField(label="แผนก")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile'):
            self.fields['role'].initial = user.profile.role
            self.fields['department'].initial = user.profile.department

    def save(self, commit=True):
        user = super().save(commit)

        profile = user.profile
        profile.role = self.cleaned_data['role']
        profile.department = self.cleaned_data['department']
        profile.save()

        return user

class UserCreateForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password"
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 != p2:
            raise forms.ValidationError("Password ไม่ตรงกัน")

        return cleaned_data
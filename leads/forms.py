from .models import*
from django import forms

class Sources_Form(forms.ModelForm):
    
    class Meta:
        model = Sources
        fields = ('name',)

class User_Profile_Form(forms.ModelForm):
    class Meta:
        model = user_profile
        fields = ('first_name', 'last_name', 'email', 'phone', 'password')

class Leads_File_Form(forms.ModelForm):

    class Meta:
        model = Leads_File
        fields = ('file', 'file_name', 'source', )


# class Leads_Form(forms.ModelForm):
#     class Meta:
#         model = Leads
#         fields= ('first_name', 'last_name', 'city', 'state',
#               'address', 'debt_amount', 'phone', 'email', 
#               'opt_in_ip', 'cost', 'purchase_date', 'import_date',)
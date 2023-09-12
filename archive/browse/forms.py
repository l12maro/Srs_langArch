from django import forms

class UploadXMLForm(forms.Form):
    xml_file = forms.FileField()

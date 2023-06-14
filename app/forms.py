from django import forms


class UploadForm(forms.Form):
    file = forms.FileField()


class BCoeffForm(forms.Form):
    b = forms.FloatField(min_value=0, max_value=1)

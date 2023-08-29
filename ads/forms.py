from django.forms import ModelForm

from .models import Ad


class AdForm(ModelForm):
    class Meta:
        model = Ad
        fields = '__all__'

    def clean(self):
        clean_data = super().clean()

        if self.instance.is_delete and clean_data.get('is_delete'):
            clean_data = {}

        return clean_data

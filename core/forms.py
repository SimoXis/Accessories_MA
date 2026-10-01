from django import forms

MOROCCAN_CITIES = (
    ('', 'Sélectionnez votre ville'),
    ('Casablanca', 'Casablanca'),
    ('Rabat', 'Rabat'),
    ('Salé', 'Salé'),
    ('Marrakech', 'Marrakech'),
    ('Fès', 'Fès'),
    ('Tanger', 'Tanger'),
    ('Agadir', 'Agadir'),
    ('Meknès', 'Meknès'),
    ('Oujda', 'Oujda'),
    ('Kénitra', 'Kénitra'),
    ('Tétouan', 'Tétouan'),
    ('Safi', 'Safi'),
    ('El Jadida', 'El Jadida'),
    ('Béni Mellal', 'Béni Mellal'),
    ('Nador', 'Nador'),
    ('Khouribga', 'Khouribga'),
    ('Settat', 'Settat'),
    ('Laâyoune', 'Laâyoune'),
    ('Dakhla', 'Dakhla'),
    ('other', 'Autre ville'),
)


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={
        'placeholder': 'Nom complet',
        'class': 'form-control',
        'autocomplete': 'name'
    }))
    phone_number = forms.RegexField(regex=r'^0[67]\d{8}$', error_messages={
        'invalid': 'Veuillez saisir un numéro marocain valide (06 ou 07 suivi de 8 chiffres).'
    }, widget=forms.TextInput(attrs={
        'placeholder': 'Téléphone',
        'class': 'form-control',
        'inputmode': 'numeric',
        'autocomplete': 'tel',
        'pattern': '0[67][0-9]{8}',
        'maxlength': '10'
    }))
    city = forms.ChoiceField(choices=MOROCCAN_CITIES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    other_city = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Précisez votre ville',
        'class': 'form-control'
    }))
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': "Adresse de livraison",
        'class': 'form-control',
        'autocomplete': 'street-address'
    }))
    submission_key = forms.CharField(max_length=64, widget=forms.HiddenInput())
    website = forms.CharField(required=False, widget=forms.HiddenInput(attrs={
        'autocomplete': 'off',
        'tabindex': '-1'
    }))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('city') == 'other':
            other_city = cleaned_data.get('other_city', '').strip()
            if not other_city:
                self.add_error('other_city', 'Veuillez préciser votre ville.')
            else:
                cleaned_data['city'] = other_city
        return cleaned_data


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()

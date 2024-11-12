from django import forms
# from captcha.fields import CaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML
from django.utils.safestring import mark_safe
from hcaptcha.fields import hCaptchaField


class ContactForm(forms.Form):
    # error message

    name = forms.CharField(
        label="Name",
        max_length=100,
        required=True,
    )

    email = forms.CharField(
        label="Email",
        max_length=100,
        required=True,
    )

    message = forms.CharField(
        widget=forms.Textarea
    )

    gdpr = forms.BooleanField(
        required=True,
        label=mark_safe('I accept the <a href="https://web.judaicalink.org/legal">Privacy Policy</a>.'),
    )

    captcha = hCaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["email"].widget.input_type = "email"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-sm-4 col-lg-2"
        self.helper.field_class = "col-sm-8 col-lg-10"

        self.helper.layout = Layout(
            Field('name', placeholder="Your Name"),
            Field('email', placeholder="Your Email"),
            Field('message', placeholder="Your Message"),
            'gdpr',
            'captcha',
            Submit('submit', 'Submit', css_class="btn-secondary bg-white"),
        )

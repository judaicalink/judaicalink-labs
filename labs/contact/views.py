import requests
import math
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings


from .forms import ContactForm
from django.core.mail import BadHeaderError, send_mail

# Create your views here.


def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():

            # send mail
            request.POST.get('name')

            subject = "New request from contact form."
            from_mail = request.POST.get('email', '')
            content = request.POST.get('message', '')
            if content and from_mail:
                try:
                    send_mail(subject, content, from_mail, [settings.EMAIL_TO], fail_silently=False, html_message=False)

                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
            return HttpResponseRedirect('sent')
    else:
        form = ContactForm()

    return render(request, 'contact/contact.html', {'form': form})

def sent(request):
    return render(request, 'contact/sent.html')
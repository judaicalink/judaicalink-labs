import requests
import math
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT


from .forms import ContactForm
from django.core.mail import BadHeaderError, send_mail

# Create your views here.
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


@cache_page(CACHE_TTL)
def index(request):
    error_message = ''
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # send mail
            name = request.POST.get('name')

            subject = "New request from Judaicalink.org."
            from_mail = request.POST.get('email', '')
            from_name_mail = '{} <{}>'.format(name, from_mail)
            content = request.POST.get('message', '')
            if content and from_mail:
                print('Sending mail')
                try:
                    print('Email to:', settings.EMAIL_TO)
                    mail_sent = send_mail(subject=subject, message=content, from_email=from_name_mail,  recipient_list=[settings.EMAIL_TO], fail_silently=False, html_message=False, auth_user=settings.EMAIL_HOST_USER, auth_password=settings.EMAIL_HOST_PASSWORD)
                    print('Mail sent:', mail_sent)
                    if mail_sent is 1:
                        print('Mail sent')
                        return HttpResponseRedirect(reverse('contact:sent'))
                    else:
                        print('Mail not sent')
                        error_message = 'Mail not sent'
                        return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})

                except BadHeaderError:
                    return HttpResponse('Invalid header found.')

                except Exception as e:
                    # email not sent
                    print('Error, Email not sent', e, now())
                    error_message = "Email not sent. Please try again."
                    return HttpResponse('Email not sent. Please try again..')
            else:
                error_message = 'Form is not valid.'

        else:
            error_message = 'Form is not valid.'
    else:
        form = ContactForm()

    return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})


@cache_page(CACHE_TTL)
def sent(request):
    return render(request, 'contact/sent.html')


def csrf_faiure(request, reason=""):
    context = {'reason': reason}
    return render(request, 'contact/csrf_failure.html', context=context)
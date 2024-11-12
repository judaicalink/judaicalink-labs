from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

from .forms import ContactForm
from django.core.mail import BadHeaderError, send_mail

# Create your views here.
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

# Contact index page
#@cache_page(CACHE_TTL)
def index(request):
    error_message = '' # Default error message

    if request.method == 'POST':
        # Process the form
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send mail
            name = request.POST.get('name')

            subject = "New request from Judaicalink.org."
            from_email = request.POST.get('email')
            from_name_email = '{} <{}>'.format(name, from_email)
            message = request.POST.get('message')

            # For debugging
            print('Name:', name)
            print('Email:', from_email)
            print('Message:', message)
            print('Subject:', subject)

            # TODO: Add hCaptcha verification
            captcha = request.POST.get('h-captcha-response')
            print('Captcha:', captcha)

            if message and from_name_email and name and captcha:
                print('Sending mail')
                try:
                    print('Email to:', settings.EMAIL_TO)
                    # Send mail
                    # TODO: change mailing system
                    #send_mail(subject=subject, message=content, from_email=from_name_mail,  recipient_list=[settings.EMAIL_TO], fail_silently=False, html_message=False, auth_user=settings.EMAIL_HOST_USER, auth_password=settings.EMAIL_HOST_PASSWORD)
                    send_mail(subject, message=message, from_email=from_name_email, recipient_list=["b.schnabel@hs-mannheim.de"], fail_silently=False)

                except BadHeaderError:
                    error_message = 'Invalid header found.'
                    return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})

                except Exception as e:
                    # email not sent
                    print('Error, Email not sent', e, now())
                    return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})

                print('Mail sent')
                return HttpResponseRedirect(reverse('contact:sent'))

            else:
                error_message = 'Form is not valid.'


        else:
            error_message = 'Form is not valid.'

    else:
        # Render the default form
        form = ContactForm()

    return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})


# Contact sent page
@cache_page(CACHE_TTL)
def sent(request):
    return render(request, 'contact/sent.html')

# CSRF failure page
def csrf_failure(request, reason=""):
    context = {'reason': reason}
    return render(request, 'contact/csrf_failure.html', context=context)
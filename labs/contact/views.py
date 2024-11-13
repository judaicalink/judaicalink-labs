import logging
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

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Contact index page
#@cache_page(CACHE_TTL)
def index(request):
    error_message = '' # Default error message

    if request.POST:
        logger.info('POST request')
        # Process the form
        form = ContactForm(request.POST)

        # Send mail
        logger.info('DEBUG: %s', settings.DEBUG)
        name = request.POST.get('name')

        subject = "New request from Judaicalink.org."
        from_email = request.POST.get('email')
        from_name_email = '{} <{}>'.format(name, from_email)
        message = request.POST.get('message')

        # For debugging
        logger.debug('Name: %s', name)
        logger.debug('Email: %s', from_email)
        logger.debug('Message: %s', message)
        logger.debug('Subject: %s', subject)

        # TODO: Add hCaptcha verification
        captcha = request.POST.get('h-captcha-response')
        logger.debug('Captcha: %s', captcha)

        # if the message, the from_email, the name and the captcha are not empty
        if message and from_email and name and captcha:
            logger.info('Sending mail')
            try:
                # Send mail
                # TODO: change mailing system
                #send_mail(subject=subject, message=content, from_email=from_name_mail,  recipient_list=[settings.EMAIL_TO], fail_silently=False, html_message=False, auth_user=settings.EMAIL_HOST_USER, auth_password=settings.EMAIL_HOST_PASSWORD)
                send_mail(subject, message=message, from_email=from_name_email, recipient_list=["b.schnabel@hs-mannheim.de"], fail_silently=False)

            except BadHeaderError:
                error_message = 'Invalid header found.'
                return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})

            except Exception as e:
                # email not sent
                logger.debug('Error, Email not sent', e)
                error_message = f'Email not sent. Please try again. {e}'
                return render(request, 'contact/contact.html', {'form': form, 'error_message': error_message})

            logger.info('Mail sent')
            return HttpResponseRedirect(reverse('contact:sent'))

        else:
            error_message = 'Form is not valid.'
            form.add_error('message', 'Please fill in the message.')
            form.add_error('email', 'Please fill in the email.')
            form.add_error('name', 'Please fill in the name.')
            form.add_error('captcha', 'Please fill in the captcha.')
            form.add_error(None, 'Please fill in all fields.')



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
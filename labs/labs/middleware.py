# middleware.py

from django.template.base import VariableDoesNotExist
from django.utils.deprecation import MiddlewareMixin

class SuppressVariableDoesNotExistMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        try:
            response.render()
        except VariableDoesNotExist as e:
            # Log or suppress the missing variable error
            print(f"Missing variable in template: {e}")
        return response

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from rest_framework.schemas import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi as yasg_openapi
from django.http import JsonResponse
from search.views import search

class SimpleSearchAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        manual_parameters=[
            yasg_openapi.Parameter('q', yasg_openapi.IN_QUERY, description="Search query", type=yasg_openapi.TYPE_STRING),
            yasg_openapi.Parameter('limit', yasg_openapi.IN_QUERY, description="Number of results", type=yasg_openapi.TYPE_INTEGER),
            yasg_openapi.Parameter('offset', yasg_openapi.IN_QUERY, description="Pagination offset", type=yasg_openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Missing query parameter ?q='}, status=400)
        results = search(request=request)

        paginator = self.pagination_class()
        paginated_results = paginator.paginate_queryset(results, request)
        return paginator.get_paginated_response(paginated_results)


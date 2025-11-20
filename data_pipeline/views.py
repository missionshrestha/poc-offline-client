# example: pipelines/views.py

from rest_framework.views import APIView
from rest_framework.response import Response

from licensing.enforcement import require_feature


class DummyProtectedView(APIView):
    @require_feature("pipeline_execution")
    def post(self, request, *args, **kwargs):
        print("DummyProtectedView called")
        grants = getattr(request, "license_grants", None)
        return Response({"message": "OK, you hit a protected endpoint.", "license_status": grants.status})

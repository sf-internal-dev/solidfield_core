from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.apps.core.models import Technician

@api_view(["GET"])
def list_technicians_api(request):
    technicians = Technician.objects.all()
    pass
    # serializer = TechnicianSerializer(technicians, many=True)
    # return Response({"technicians": serializer.data}, status=status.HTTP_200_OK)

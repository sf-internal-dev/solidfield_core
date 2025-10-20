from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.apps.core.models import Technician
from backend.apps.core.api.serializers.core_serializers import TechnicianSerializer

@api_view(["GET"])
def list_technicians_api(request):
    technicians = Technician.objects.all()

    serializer = TechnicianSerializer(technicians, many=True)
    return Response({"technicians": serializer.data}, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_technician_api(request, technician_id):
    try:
        technician = Technician.objects.get(id=technician_id)
    except Technician.DoesNotExist:
        return Response({"error": "Technician not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TechnicianSerializer(technician)
    return Response({"technician": serializer.data}, status=status.HTTP_200_OK)
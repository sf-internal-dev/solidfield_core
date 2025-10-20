from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.apps.clients.models import Client
from backend.apps.clients.api.serializers.client_serializers import ClientSerializer

@api_view(["GET"])
def list_clients_api(request):
    clients = Client.objects.all()

    serializer = ClientSerializer(clients, many=True)
    return Response({"clients": serializer.data}, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_client_api(request, client_id):
    try:
        client = ClientSerializer.objects.get(id=client_id)
    except ClientSerializer.DoesNotExist:
        return Response({"error": "Clients not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ClientSerializer(client)
    return Response({"client": serializer.data}, status=status.HTTP_200_OK)
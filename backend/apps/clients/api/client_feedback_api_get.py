from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.apps.clients.models import ClientFeedback, FeedbackLink
from backend.apps.clients.api.serializers.client_serializers import ClientFeedbackSerializer, FeedbackLinkSerializer


@api_view(["GET"])
def list_clients_feedback_api(request):
    clients_feedback = ClientFeedback.objects.all()

    serializer = ClientFeedbackSerializer(clients_feedback, many=True)
    return Response({"clients feedback": serializer.data}, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_client_feedback_api(request, client_id):
    try:
        client = ClientFeedback.objects.get(id=client_id)
    except ClientFeedbackSerializer.DoesNotExist:
        return Response({"error": "Client Feedback not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ClientFeedbackSerializer(client)
    return Response({"client feedback": serializer.data}, status=status.HTTP_200_OK)

# @api_view(["GET"])
# def get_feedback_link_api(request, client_id):
#     try:
#         client = ClientFeedback.objects.get(id=client_id)
#     except ClientFeedbackSerializer.DoesNotExist:
#         return Response({"error": "Client Feedback not found"}, status=status.HTTP_404_NOT_FOUND)
    
#     serializer = ClientFeedbackSerializer(client)
#     return Response({"client feedback": serializer.data}, status=status.HTTP_200_OK)


from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False, allow_null=True)
    message = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    reply = serializers.CharField()

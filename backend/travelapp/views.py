import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# print(sys.path) 

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatSession, Message
from chatbot.serializers import ChatRequestSerializer, ChatResponseSerializer
from chatbot.agenticai.agent import build_agent
from langchain_core.messages import HumanMessage, AIMessage

agent = build_agent()

class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data.get('session_id')
            message_text = serializer.validated_data['message']

            # Create or fetch chat session
            session, created = ChatSession.objects.get_or_create(session_id=session_id) if session_id else ChatSession.objects.get_or_create()

            # Save user's message
            Message.objects.create(session=session, role='user', content=message_text)

            # Load past messages
            past_messages = Message.objects.filter(session=session).order_by("created_at")
            history = []
            for msg in past_messages:
                if msg.role == 'user':
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))

            # Run LangGraph agent
            result = agent.invoke({"messages": history})
            reply_text = result["messages"][-1].content

            # Save assistant's response
            Message.objects.create(session=session, role='assistant', content=reply_text)

            response_data = {
                "session_id": str(session.session_id),
                "reply": reply_text
            }
            return Response(ChatResponseSerializer(response_data).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

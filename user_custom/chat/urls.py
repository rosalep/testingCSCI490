from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_page, name='chat_page'),
    path('updates/', views.new_message, name='get_updates'),
    path('send/', views.send_message, name='send_update'),
]
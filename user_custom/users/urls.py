from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf import settings
urlpatterns = [
    path('', views.home, name='user-home'), # temp home 
    path('login/', views.login_page, name='user-login'),
    path('signup/', views.signup, name='user-signup'),
    path('profile/', views.profile, name='user-profile'),
    path('logout/', views.logout_view, name='user-logout'),
    path('profile/edit/', views.profileUpdate, name='user-profile-update'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
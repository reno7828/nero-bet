from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views as core_views
from django.contrib import messages

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),

    # Correction Logout : On s'assure qu'il redirige bien vers 'login'
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('register/', core_views.register, name='register'),

    # App logic
    path('', core_views.dashboard, name='dashboard'),
    path('setup-api/', core_views.setup_api, name='setup_api'),

    #Mentions
    path('mentions-legales/', core_views.mentions_legales, name='mentions_legales'),
    path('conditions/', core_views.conditions, name='conditions'),
    path('contact/', core_views.contact, name='contact'),


]
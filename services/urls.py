from django.urls import path, include
from . import views
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path('social-auth/', include('social_django.urls', namespace='social')),

    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('main/', views.main_view, name='main'),
    path('profile/', views.profile_view, name = 'profile'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('help_walk/', views.help_walk, name='help_walk'),
    path('existing_appointment/', views.existing_appointment, name='existing_appointment'),
    path('view_appointment/<int:appointment_id>/', views.view_appointment, name='view_appointment'),
    path('other_profile/<str:username>/', views.other_profile_view, name='other_profile'),
    path("update_appointment_status/", views.update_appointment_status, name="update_appointment_status"),
    path('api/appointments/', views.get_appointments, name='get_appointments'),
    path('api/appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:appointment_id>/mark_read/', views.mark_notification_read, name='mark_notification_read'),
    path('appointments/<int:appointment_id>/submit_review/', views.submit_review, name='submit_review'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
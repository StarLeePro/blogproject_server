from django.urls import path
from . import views

urlpatterns = [
    # v1/users/sms
    path('sms', views.sms_view),

    path('<str:username>', views.UserViews.as_view()),
    path('<str:username>/avatar', views.users_views)
]
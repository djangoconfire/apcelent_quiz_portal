from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = format_suffix_patterns([
    url(r'^quiz_list/$', views.QuizList.as_view(), name='quiz-list'),
    url(r'^quiz/(?P<pk>[0-9]+)/$', views.QuizList.as_view(), name='QuizList-detail'),
    url(r'^user_profile_list/$', views.UserProfileList.as_view(), name='user_profile-list'),
])
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings

urlpatterns = [
    
    # admin url 
    url(r'^admin/', include(admin.site.urls)),

    # app_urls
    url(r'^',include('quiz.urls',namespace="quiz")), 

    # for api
    url(r'^api/', include('api.urls',namespace="api")),   
]

# for staticfiles
urlpatterns +=[
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
]
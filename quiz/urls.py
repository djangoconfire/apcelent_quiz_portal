from django.conf.urls import include, url

urlpatterns = [
    url(r'^$', 'quiz.views.home',name="home"),
    url(r'^quizzes/$', 'quiz.views.quizlist_user',name="quizzes"),
	url(r'^register/$', 'quiz.views.user_register',name="register"),
    url(r'^start/$', 'quiz.views.start',name="start_quiz"),
    url(r'^start/(?P<attempt_num>\d+)/(?P<questionpaper_id>\d+)/$', 'quiz.views.start'),
    url(r'^intro/(?P<questionpaper_id>\d+)/$', 'quiz.views.intro'),    
    url(r'^intro/$', 'quiz.views.start',name="intro"),
    url(r'^results/$', 'quiz.views.results_user',name="result"),
    url(r'^complete/$', 'quiz.views.complete',name="complete"),
    url(r'^complete/(?P<attempt_num>\d+)/(?P<questionpaper_id>\d+)/$',\
            'quiz.views.complete'),
    url(r'^manage/$', 'quiz.views.prof_manage',name="manage"),
    url(r'^manage/addquiz/$', 'quiz.views.add_quiz',name="add_quiz"),
    url(r'^manage/editquiz/$', 'quiz.views.edit_quiz',name="edit_quiz"),
    url(r'^manage/showquiz/$', 'quiz.views.show_all_quiz',name="show_quiz"),
    url(r'^manage/monitor/$', 'quiz.views.monitor',name="monitor"),
    
    
]

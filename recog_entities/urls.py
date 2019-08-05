from django.conf.urls import url
from recog_entities import views

urlpatterns = [
    url(r'^$', views.index, name='home'),
    url(r'^process/', views.process, name='process'),
]

"""image URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from image_app import views
# from django.conf.urls import include
# from django.contrib import admin


urlpatterns = [
    # url(r'^$', views.listing, name='list'),
    # e.g., .../image_app/sampletab1/1/ for details about the donor
    # url(r'^sampletab1/(?P<pk>[0-9]+)/$', views.sampletab1,
    #      name='sampletab1'),
    url(r'^sampletab1/$', views.sampletab1, name='sampletab1'),
    url(r'^sampletab2/$', views.sampletab2, name='sampletab2'),
    url(r'^check_metadata/$', views.check_metadata, name='check_metadata'),
    url(r'^model_form_upload/$', views.model_form_upload,
        name='model_form_upload'),
    url(r'dump_reading/$', views.dump_reading, name='dump_reading'),
    url(r'dump_reading2/$', views.dump_reading2, name='dump_reading2'),
    url(r'truncate_image_tables/$', views.truncate_image_tables, name='truncate_image_tables'),
    url(r'truncate_cryoweb_tables/$', views.truncate_cryoweb_tables, name='truncate_cryoweb_tables'),
    url(r'truncate_databases/$', views.truncate_databases, name='truncate_databases'),

]
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
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

# importing image views
from uid.views import (
    AboutView, IndexView, protected_view, TermsView, PrivacyView,
    AboutUploadingView, AboutSubmissionView)

# renaming admin app (login, admin brand and page title)
# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/change_text.html
admin.site.site_header = "IMAGE InjectTool Admin"
admin.site.site_title = "IMAGE InjectTool Admin Portal"
admin.site.index_title = "Welcome to IMAGE InjectTool Admin"

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^about/$', AboutView.as_view(), name='about'),
    url(r'^privacy/$', PrivacyView.as_view(), name='privacy-policy'),
    url(r'^terms/$', TermsView.as_view(), name='terms-and-conditions'),
    url(r'^submitting-data-into-biosamples/$',
        AboutUploadingView.as_view(),
        name='about-uploading'),
    url(r'^the-injecttool-submission-system/$',
        AboutSubmissionView.as_view(),
        name='about-submission'),
    url(r"^protected/(?P<path>.*)$",
        protected_view),
    url(r'^login/$',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html'),
        name='login'),
    url(r'^logout/$',
        auth_views.LogoutView.as_view(
            template_name='accounts/logged_out.html'),
        name='logout'),
    url(r'^uid/',
        include(
            ('uid.urls', 'uid'),
            namespace="uid")),
    url(r'^language/',
        include(
            ('language.urls', 'language'),
            namespace="language")),
    url(r'^biosample/',
        include(
            ('biosample.urls', 'biosample'),
            namespace="biosample")),
    url(r'^accounts/',
        include(
            ('accounts.urls', 'accounts'),
            namespace="accounts")),
    url(r'^validation/',
        include(
            ('validation.urls', 'validation'),
            namespace="validation")),
    url(r'^submissions/',
        include(
            ('submissions.urls', 'submissions'),
            namespace="submissions")),
    url(r'^animals/',
        include(
            ('animals.urls', 'animals'),
            namespace='animals')),
    url(r'^samples/',
        include(
            ('samples.urls', 'samples'),
            namespace='samples')),
    url(r'^zooma/',
        include(
            ('zooma.urls', 'zooma'),
            namespace='zooma')),
]

# Activate django-debug-toolbar only when settings.DEBUG is True
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

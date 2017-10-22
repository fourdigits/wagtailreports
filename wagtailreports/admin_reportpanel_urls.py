from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtailreports.views import reportpanels

urlpatterns = [
    url(r'^$', reportpanels.index, name='index'),
    url(r'^add/$', reportpanels.add, name='add'),
    url(r'^edit/(\d+)/$', reportpanels.edit, name='edit'),
    url(r'^delete/(\d+)/$', reportpanels.delete, name='delete'),
    # url(r'^usage/(\d+)/$', reportpanels.usage, name='reportpanel_usage'),
]

from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtailreports.views import reports

urlpatterns = [
    url(r'^$', reports.index, name='index'),
    url(r'^add/$', reports.add, name='add'),
    url(r'^edit/(\d+)/$', reports.edit, name='edit'),
    url(r'^delete/(\d+)/$', reports.delete, name='delete'),
    # url(r'^usage/(\d+)/$', reports.usage, name='report_usage'),
]

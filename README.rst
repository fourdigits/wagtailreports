Wagtail Reports
===============

Display filtered content on the admin dashboard.


Install
-------

Pip install:

    pip install git+ssh://git@github.com/fourdigits/wagtailreports.git


Add 'wagtailreports' to your settings:

    INSTALLED_APPS = [
        ...
        'wagtailreports',
    ]


Include the `wagtailreports_urls` in your urls:

    from wagtailreports import urls as wagtailreports_urls

    urlpatterns = [
        ...
        url(r'^reports/', include(wagtailreports_urls)),

    ]


Development install



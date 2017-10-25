Wagtail Reports
===============

Wagtail Reports allows to create custom reports. The reports are displayed on the admin dashboard.
Wagtail Reports gives you and your team useful insight on the day-to-day content and content changes.


Install
-------

Pip install:

.. code-block:: bash

    pip install git+ssh://git@github.com/fourdigits/wagtailreports.git


Add wagtailreports to your settings:

.. code:: python

    INSTALLED_APPS = [
        ...
        'wagtailreports',
    ]


Include the wagtailreports_urls in your urls:

.. code:: python

    from wagtailreports import urls as wagtailreports_urls

    urlpatterns = [
        ...
        url(r'^reports/', include(wagtailreports_urls)),

    ]

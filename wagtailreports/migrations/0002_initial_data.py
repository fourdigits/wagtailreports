# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import VERSION as DJANGO_VERSION
from django.db import migrations


def add_report_permissions_to_admin_groups(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')

    # Get report permissions
    report_content_type, _created = ContentType.objects.get_or_create(
        model='report',
        app_label='wagtailreports',
        defaults={'name': 'report'} if DJANGO_VERSION < (1, 8) else {}
    )

    add_report_permission, _created = Permission.objects.get_or_create(
        content_type=report_content_type,
        codename='add_report',
        defaults={'name': 'Can add report'}
    )
    change_report_permission, _created = Permission.objects.get_or_create(
        content_type=report_content_type,
        codename='change_report',
        defaults={'name': 'Can change report'}
    )
    delete_report_permission, _created = Permission.objects.get_or_create(
        content_type=report_content_type,
        codename='delete_report',
        defaults={'name': 'Can delete report'}
    )

    # Assign it to Editors and Moderators groups
    for group in Group.objects.filter(name__in=['Editors', 'Moderators']):
        group.permissions.add(add_report_permission, change_report_permission, delete_report_permission)


def remove_report_permissions(apps, schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    report_content_type = ContentType.objects.get(
        model='report',
        app_label='wagtailreports',
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=report_content_type,
        codename__in=('add_report', 'change_report', 'delete_report'),
    ).delete()


def add_report_panel_permissions_to_admin_groups(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')

    # Get report panel permissions
    report_panel_content_type, _created = ContentType.objects.get_or_create(
        model='report_panel',
        app_label='wagtailreports',
        defaults={'name': 'report panel'} if DJANGO_VERSION < (1, 8) else {}
    )

    add_report_panel_permission, _created = Permission.objects.get_or_create(
        content_type=report_panel_content_type,
        codename='add_report_panel',
        defaults={'name': 'Can add report panel'}
    )
    change_report_panel_permission, _created = Permission.objects.get_or_create(
        content_type=report_panel_content_type,
        codename='change_report_panel',
        defaults={'name': 'Can change report panel'}
    )
    delete_report_panel_permission, _created = Permission.objects.get_or_create(
        content_type=report_panel_content_type,
        codename='delete_report_panel',
        defaults={'name': 'Can delete report panel'}
    )

    # Assign it to Editors and Moderators groups
    for group in Group.objects.filter(name__in=['Editors', 'Moderators']):
        group.permissions.add(add_report_panel_permission, change_report_panel_permission, delete_report_panel_permission)


def remove_report_panel_permissions(apps, schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    report_panel_content_type = ContentType.objects.get(
        model='report_panel',
        app_label='wagtailreports',
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=report_panel_content_type,
        codename__in=('add_report_panel', 'change_report_panel', 'delete_report_panel'),
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailreports', '0001_initial'),

        # Need to run wagtailcores initial data migration to make sure the groups are created
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(add_report_permissions_to_admin_groups, remove_report_permissions),
        migrations.RunPython(add_report_panel_permissions_to_admin_groups, remove_report_panel_permissions),
    ]

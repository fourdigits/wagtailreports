from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import (
    PermissionPolicyChecker, permission_denied, popular_tags_for_model)
from wagtail.wagtailsearch import index as search_index

from wagtailreports.forms import get_report_form
from wagtailreports.models import get_report_model
from wagtailreports.permissions import report_permission_policy as permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    Report = get_report_model()

    # Get reports (filtered by user permission)
    reports = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    )

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
    reports = reports.order_by(ordering)

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search reports"))
        if form.is_valid():
            query_string = form.cleaned_data['q']
            reports = reports.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search reports"))

    # Pagination
    paginator, reports = paginate(request, reports)

    # Create response
    if request.is_ajax():
        return render(request, 'wagtailreports/reports/results.html', {
            'ordering': ordering,
            'reports': reports,
            'query_string': query_string,
            'is_searching': bool(query_string),
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })
    else:
        return render(request, 'wagtailreports/reports/index.html', {
            'ordering': ordering,
            'reports': reports,
            'query_string': query_string,
            'is_searching': bool(query_string),
            'search_form': form,
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('add')
def add(request):
    Report = get_report_model()
    ReportForm = get_report_form(Report)

    if request.method == 'POST':
        report = Report()
        form = ReportForm(request.POST, instance=report)  #user=request.user
        if form.is_valid():
            form.save()

            # Reindex the report to make sure all tags are indexed
            search_index.insert_or_update_object(report)

            messages.success(request, _("Report '{0}' added.").format(report.title), buttons=[
                messages.button(reverse('wagtailreports:edit', args=(report.id,)), _('Edit'))
            ])
            return redirect('wagtailreports:index')
        else:
            messages.error(request, _("The report could not be saved due to errors."))
    else:
        form = ReportForm()

    return render(request, "wagtailreports/reports/add.html", {
        'form': form,
    })


@permission_checker.require('change')
def edit(request, report_id):
    Report = get_report_model()
    ReportForm = get_report_form(Report)

    report = get_object_or_404(Report, id=report_id)

    # if not permission_policy.user_has_permission_for_instance(request.user, 'change', report):
    #     return permission_denied(request)

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report) # user=request.user
        if form.is_valid():
            report = form.save()

            # Reindex the report to make sure all tags are indexed
            search_index.insert_or_update_object(report)

            messages.success(request, _("Report '{0}' updated").format(report.title), buttons=[
                messages.button(reverse('wagtailreports:edit', args=(report.id,)), _('Edit'))
            ])
            return redirect('wagtailreports:index')
        else:
            messages.error(request, _("The report could not be saved due to errors."))
    else:
        form = ReportForm(instance=report)  #, user=request.user

    return render(request, "wagtailreports/reports/edit.html", {
        'report': report,
        'form': form,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', report
        ),
    })


@permission_checker.require('delete')
def delete(request, report_id):
    Report = get_report_model()
    report = get_object_or_404(Report, id=report_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', report):
        return permission_denied(request)

    if request.method == 'POST':
        report.delete()
        messages.success(request, _("Report '{0}' deleted.").format(report.title))
        return redirect('wagtailreports:index')

    return render(request, "wagtailreports/reports/confirm_delete.html", {
        'report': report,
    })


def usage(request, report_id):
    Report = get_report_model()
    report = get_object_or_404(Report, id=report_id)

    paginator, used_by = paginate(request, report.get_usage())

    return render(request, "wagtailreports/reports/usage.html", {
        'report': report,
        'used_by': used_by
    })

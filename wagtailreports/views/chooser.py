from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.utils import PermissionPolicyChecker
from wagtail.wagtailcore import hooks
from wagtailreports.forms import get_report_form
from wagtailreports.models import get_report_model
from wagtailreports.permissions import report_permission_policy as permission_policy
from wagtail.wagtailsearch import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


def get_report_json(report):
    """
    helper function: given a report, return the json to pass back to the
    chooser panel
    """

    return json.dumps({
        'id': report.id,
        'title': report.title,
        'url': report.url,
        'edit_link': reverse('wagtailreports:edit', args=(report.id,)),
    })


def chooser(request):
    Report = get_report_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        ReportForm = get_report_form(Report)
        uploadform = ReportForm(user=request.user)
    else:
        uploadform = None

    reports = Report.objects.all()

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_report_chooser_queryset'):
        reports = hook(reports, request)

    q = None
    if 'q' in request.GET or 'p' in request.GET:

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            reports = reports.search(q)
            is_searching = True
        else:
            reports = reports.order_by('-created_at')
            is_searching = False

        # Pagination
        paginator, reports = paginate(request, reports, per_page=10)

        return render(request, "wagtailreports/chooser/results.html", {
            'reports': reports,
            'query_string': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        reports = reports.order_by('-created_at')
        paginator, reports = paginate(request, reports, per_page=10)

        return render_modal_workflow(request, 'wagtailreports/chooser/chooser.html', 'wagtailreports/chooser/chooser.js', {
            'reports': reports,
            'uploadform': uploadform,
            'searchform': searchform,
            'is_searching': False,
        })


def report_chosen(request, report_id):
    report = get_object_or_404(get_report_model(), id=report_id)

    return render_modal_workflow(
        request, None, 'wagtailreports/chooser/report_chosen.js',
        {'report_json': get_report_json(report)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    Report = get_report_model()
    ReportForm = get_report_form(Report)

    if request.method == 'POST':
        report = Report(created_by_user=request.user)
        form = ReportForm(request.POST, request.FILES, instance=report, user=request.user)

        if form.is_valid():
            form.save()

            # Reindex the report to make sure all tags are indexed
            search_index.insert_or_update_object(report)

            return render_modal_workflow(
                request, None, 'wagtailreports/chooser/report_chosen.js',
                {'report_json': get_report_json(report)}
            )
    else:
        form = ReportForm(user=request.user)

    reports = Report.objects.order_by('title')

    return render_modal_workflow(
        request, 'wagtailreports/chooser/chooser.html', 'wagtailreports/chooser/chooser.js',
        {'reports': reports, 'uploadform': form}
    )

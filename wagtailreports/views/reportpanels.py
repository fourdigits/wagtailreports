from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import PermissionPolicyChecker, permission_denied
from wagtailreports.forms import get_report_panel_form
from wagtailreports.models import get_report_panel_model
from wagtailreports.permissions import report_panel_permission_policy as permission_policy
from wagtail.wagtailsearch import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    ReportPanel = get_report_panel_model()

    # Get panels (filtered by user permission)
    report_panels = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    )

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
        report_panels = report_panels.order_by(ordering)

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search report panels"))
        if form.is_valid():
            query_string = form.cleaned_data['q']
            report_panels = report_panels.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search report panels"))

    # Pagination
    paginator, report_panels = paginate(request, report_panels)

    # Create response
    if request.is_ajax():
        return render(request, 'wagtailreports/report_panels/results.html', {
            'ordering': ordering,
            'report_panels': report_panels,
            'query_string': query_string,
            'is_searching': bool(query_string),
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })
    else:
        return render(request, 'wagtailreports/report_panels/index.html', {
            'ordering': ordering,
            'report_panels': report_panels,
            'query_string': query_string,
            'is_searching': bool(query_string),
            'search_form': form,
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('add')
def add(request):
    ReportPanel = get_report_panel_model()
    ReportPanelForm = get_report_panel_form(ReportPanel)

    if request.method == 'POST':
        report_panel = ReportPanel()
        form = ReportPanelForm(request.POST, instance=report_panel)  # TODO: user=request.user
        if form.is_valid():
            form.save()

            # Reindex the report to make sure all tags are indexed
            search_index.insert_or_update_object(report_panel)

            messages.success(request, _("ReportPanel '{0}' added.").format(report_panel.title), buttons=[
                messages.button(reverse('wagtailreportpanels:edit', args=(report_panel.id,)), _('Edit'))
            ])
            return redirect('wagtailreportpanels:index')
        else:
            messages.error(request, _("The report could not be saved due to errors."))
    else:
        form = ReportPanelForm()

    return render(request, "wagtailreports/report_panels/add.html", {
        'form': form,
    })


@permission_checker.require('change')
def edit(request, report_id):
    ReportPanel = get_report_panel_model()
    ReportPanelForm = get_report_panel_form(ReportPanel)

    report_panel = get_object_or_404(ReportPanel, id=report_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', report_panel):
        return permission_denied(request)

    if request.method == 'POST':
        form = ReportPanelForm(request.POST, request.FILES, instance=report_panel) # user=request.user
        if form.is_valid():
            report = form.save()

            # Reindex the report to make sure all tags are indexed
            search_index.insert_or_update_object(report)

            messages.success(request, _("ReportPanel '{0}' updated").format(report.title), buttons=[
                messages.button(reverse('wagtailreportpanels:edit', args=(report.id,)), _('Edit'))
            ])
            return redirect('wagtailreportpanels:index')
        else:
            messages.error(request, _("The report panel could not be saved due to errors."))
    else:
        form = ReportPanelForm(instance=report_panel)  # TODO: user=request.user

    return render(request, "wagtailreports/report_panels/edit.html", {
        'report_panel': report_panel,
        'form': form,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', report_panel
        ),
    })


@permission_checker.require('delete')
def delete(request, report_panel_id):
    ReportPanel = get_report_panel_model()
    report_panel = get_object_or_404(ReportPanel, id=report_panel_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', report_panel):
        return permission_denied(request)

    if request.method == 'POST':
        report_panel.delete()
        messages.success(request, _("ReportPanel '{0}' deleted.").format(report_panel.title))
        return redirect('wagtailreportpanels:index')

    return render(request, "wagtailreports/report_panels/confirm_delete.html", {
        'report_panel': report_panel,
    })


def usage(request, panel_id):
    ReportPanel = get_report_panel_model()
    panel = get_object_or_404(ReportPanel, id=panel_id)

    paginator, used_by = paginate(request, panel.get_usage())

    return render(request, "wagtailreports/report_panels/usage.html", {
        'panel': panel,
        'used_by': used_by
    })

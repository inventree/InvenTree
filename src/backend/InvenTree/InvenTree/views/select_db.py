"""View that allows the user to choose a database when multiple exist."""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from InvenTree.InvenTree.tenant import (
    get_available_databases,
    get_dbfilter_pattern,
    set_current_database,
)


@require_http_methods(["GET", "POST"])
def select_database(request):
    """Allow the user to pick the active database for the session."""

    if get_dbfilter_pattern():
        return redirect(reverse('index'))

    databases = get_available_databases()

    if not databases:
        return redirect(reverse('index'))

    if len(databases) == 1:
        database = databases[0]
        request.session['tenant_database'] = database
        set_current_database(database)
        return redirect(request.GET.get('next') or reverse('index'))

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('index')

    context = {
        'databases': databases,
        'selected_database': request.session.get('tenant_database'),
        'next_url': next_url,
    }

    if request.method == 'POST':
        database = request.POST.get('database')
        if database and database in databases:
            request.session['tenant_database'] = database
            set_current_database(database)
            return HttpResponseRedirect(next_url)
        context['error'] = True

    return render(request, 'select_db.html', context)

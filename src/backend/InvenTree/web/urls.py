"""URLs for web app."""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from rest_framework import permissions, serializers

from InvenTree.mixins import RetrieveUpdateAPI


class RedirectAssetView(TemplateView):
    """View to redirect to static asset."""

    def get(self, request, *args, **kwargs):
        """Redirect to static asset."""
        return redirect(
            f'{settings.STATIC_URL}web/assets/{kwargs["path"]}', permanent=True
        )


class PreferredSerializer(serializers.Serializer):
    """Serializer for the preferred serializer session setting."""

    preferred_method = serializers.ChoiceField(choices=['cui', 'pui'])
    pui = serializers.SerializerMethodField(read_only=True)
    cui = serializers.SerializerMethodField(read_only=True)

    def get_pui(self, obj) -> bool:
        """Return true if preferred method is PUI."""
        return obj['preferred_method'] == 'pui'

    def get_cui(self, obj) -> bool:
        """Return true if preferred method is CUI."""
        return obj['preferred_method'] == 'cui'

    class Meta:
        """Meta class for PreferedSerializer."""

        fields = '__all__'


class PreferredUiView(RetrieveUpdateAPI):
    """Set preferred UI (CIU/PUI)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PreferredSerializer
    http_method_names = ['get', 'post', 'put', 'head', 'options']

    def retrieve(self, request, *args, **kwargs):
        """Retrieve the preferred UI method."""
        session = self.request.session
        session['preferred_method'] = session.get('preferred_method', 'cui')
        serializer = self.get_serializer(data=dict(session))
        serializer.is_valid(raise_exception=True)
        return JsonResponse(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update the preferred UI method."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        # Run update
        session = self.request.session
        session['preferred_method'] = serializer.validated_data['preferred_method']
        session.modified = True

        return JsonResponse(serializer.data)


spa_view = ensure_csrf_cookie(TemplateView.as_view(template_name='web/index.html'))
assets_path = path('assets/<path:path>', RedirectAssetView.as_view())


urlpatterns = [
    path(
        f'{settings.FRONTEND_URL_BASE}/',
        include([
            assets_path,
            path(
                'set-password?uid=<uid>&token=<token>',
                spa_view,
                name='password_reset_confirm',
            ),
            re_path('.*', spa_view),
        ]),
    ),
    assets_path,
    path(settings.FRONTEND_URL_BASE, spa_view, name='platform'),
]

api_urls = [
    # UI Preference
    path('ui_preference/', PreferredUiView.as_view(), name='api-ui-preference')
]

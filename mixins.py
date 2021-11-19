from rest_framework import viewsets


class SessionExpiryResetViewSetMixin(viewsets.ViewSetMixin):

    def initialize_request(self, request, *args, **kwargs):
        if str(request.user) != 'AnonymousUser':
            request.session.set_expiry(30 * 60)
        return super().initialize_request(request, *args, **kwargs)

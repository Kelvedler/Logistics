from rest_framework import permissions


class GroupBasePermission(permissions.BasePermission):
    allow_get_for = ['all']
    allow_post_for = []
    allow_put_for = []
    allow_delete_for = []

    def get_method_group_dict(self):
        return {'GET': self.allow_get_for, 'POST': self.allow_post_for, 'PUT': self.allow_put_for, 'DELETE': self.allow_delete_for}

    def has_permission(self, request, view):
        method_group_dict = self.get_method_group_dict()
        if request.method not in method_group_dict:
            self.message = 'Permission denied, method is not allowed'
            return False
        allowed_groups = method_group_dict[request.method]
        if 'all' in allowed_groups:
            return True
        elif str(request.user) == 'AnonymousUser':
            return False
        if request.user.group not in allowed_groups:
            return False
        return True

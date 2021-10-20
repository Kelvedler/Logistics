from rest_framework import permissions
from users.models import USER_GROUPS


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
        if request.user.group not in allowed_groups:
            return False
        return True


class VehiclePermission(GroupBasePermission):
    allow_get_for = [USER_GROUPS['Driver'], USER_GROUPS['Operator'], USER_GROUPS['Administrator']]
    allow_post_for = [USER_GROUPS['Driver'], USER_GROUPS['Operator'], USER_GROUPS['Administrator']]
    allow_put_for = [USER_GROUPS['Driver'], USER_GROUPS['Operator'], USER_GROUPS['Administrator']]
    allow_delete_for = [USER_GROUPS['Operator'], USER_GROUPS['Administrator']]

    def has_object_permission(self, request, view, obj):
        if request.user.group == USER_GROUPS['Operator']:
            return True
        elif request.user.group != USER_GROUPS['Driver']:
            return False
        if request.data.get('driver') != request.user.id or (obj is not None and obj.driver.id != request.user.id):
            self.message = 'Permission denied, driver can only register/edit his/her own vehicle'
            return False
        return True
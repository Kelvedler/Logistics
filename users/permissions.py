from .models import USER_GROUPS
from permissions import GroupBasePermission


class UserPermission(GroupBasePermission):
    allow_get_for = [USER_GROUPS['Customer'], USER_GROUPS['Driver'], USER_GROUPS['Operator'], USER_GROUPS['Administrator']]
    allow_put_for = [USER_GROUPS['Customer'], USER_GROUPS['Driver'], USER_GROUPS['Operator'], USER_GROUPS['Administrator']]
    allow_delete_for = [USER_GROUPS['Administrator']]

    def has_object_permission(self, request, view, obj):
        if request.user.group in [USER_GROUPS['Operator'], USER_GROUPS['Administrator']] and request.method == 'GET':
            return True
        elif request.user.group == USER_GROUPS['Administrator'] and request.method == 'PUT':
            return True
        elif request.user.id == getattr(obj, 'id', None):
            return True
        return False

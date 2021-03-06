from users.models import USER_GROUPS
from permissions import GroupBasePermission


class VehiclePermission(GroupBasePermission):
    allow_post_for = [USER_GROUPS['Driver'], USER_GROUPS['Operator']]
    allow_put_for = [USER_GROUPS['Driver'], USER_GROUPS['Operator']]
    allow_delete_for = [USER_GROUPS['Operator']]

    def has_object_permission(self, request, view, obj):
        if request.user.group == USER_GROUPS['Operator']:
            return True
        elif request.user.group != USER_GROUPS['Driver']:
            return False
        if request.data.get('driver') != request.user.id or (obj is not None and obj.driver.id != request.user.id):
            self.message = 'Permission denied, driver can only register/edit his/her own vehicle'
            return False
        return True


class OrderPermission(GroupBasePermission):
    allow_get_for = [USER_GROUPS['Customer'], USER_GROUPS['Driver'], USER_GROUPS['Operator']]
    allow_post_for = [USER_GROUPS['Customer']]
    allow_put_for = [USER_GROUPS['Customer']]
    allow_delete_for = [USER_GROUPS['Customer'], USER_GROUPS['Operator']]

    def has_object_permission(self, request, view, obj):
        if request.method in ['POST', 'PUT']:
            if request.user.id != request.data.get('customer'):
                self.message = 'Permission denied, customer can only place order on his/her name'
                return False
        elif request.method in ['GET', 'DELETE']:
            if request.user.group == USER_GROUPS['Customer'] and request.user.id != obj.get('customer_id'):
                error_dict = {'GET': 'view', 'DELETE': 'delete'}
                self.message = 'Permission denied, customer can {} only his/her own orders.'.format(
                    error_dict[request.method])
                return False
            elif request.user.group == USER_GROUPS['Driver'] and request.user.id != obj.get('driver_id'):
                self.message = 'Permission denied, driver can only view orders placed on his/her vehicle'
                return False
        return True


class LocationPermission(GroupBasePermission):
    allow_post_for = [USER_GROUPS['Operator']]
    allow_put_for = [USER_GROUPS['Operator']]
    allow_delete_for = [USER_GROUPS['Operator']]


class RoutePermission(GroupBasePermission):
    allow_post_for = [USER_GROUPS['Customer']]
    allow_delete_for = [USER_GROUPS['Operator'], USER_GROUPS['Administrator']]


class CompleteRoutePermission(GroupBasePermission):
    allow_get_for = [USER_GROUPS['Customer'], USER_GROUPS['Driver'], USER_GROUPS['Operator'],
                     USER_GROUPS['Administrator']]
    allow_post_for = [USER_GROUPS['Driver']]

    def has_object_permission(self, request, view, obj):
        if request.method == 'POST' and request.user.id != obj.get('driver_id'):
            self.message = 'Permission denied, driver can only complete his/her own routes'
            return False
        elif request.user.group == USER_GROUPS['Customer'] and request.user.id != obj.get('customer_id'):
            self.message = 'Permission denied, customer can view only his/her own orders'
            return False
        elif request.user.group == USER_GROUPS['Driver'] and request.user.id != obj.get('driver_id'):
            self.message = 'Permission denied, driver can only view orders completed by him/her'
            return False
        return True

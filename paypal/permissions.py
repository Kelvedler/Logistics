from users.models import USER_GROUPS
from permissions import GroupBasePermission


class OrderPermission(GroupBasePermission):
    allow_post_for = [USER_GROUPS['Customer']]

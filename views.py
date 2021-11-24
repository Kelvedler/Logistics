import re


def exclude_fields(fields, exclude):
    return_fields = {}
    for field, nested_field in fields.items():
        if field not in exclude:
            if nested_field is not None:
                nested_exclude = [re.search(r'{}__(.+)'.format(field), exclude_item).group(1) for exclude_item in
                                  exclude if re.search(r'{}__(.+)'.format(field), exclude_item)]
                return_fields[field] = exclude_fields(nested_field, nested_exclude)
            else:
                return_fields[field] = None
    return return_fields
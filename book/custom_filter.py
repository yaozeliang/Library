from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter("has_group")
def has_group(user, group_name):
    if getattr(user, "is_superuser", False):
        return True
    groups = user.groups.all().values_list("name", flat=True)
    return group_name in groups

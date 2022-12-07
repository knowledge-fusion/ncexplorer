from flask_admin import BaseView
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.contrib.mongoengine.filters import (
    FilterInList,
    FilterNotInList,
    ReferenceObjectIdFilter,
)
from flask_login import current_user
from mongoengine import DictField, ListField, ObjectIdField


class AuthView(BaseView):
    def is_accessible(self):
        res = current_user.is_authenticated
        return res


class AuthModelView(ModelView):
    can_export = True
    can_view_details = True
    details_template = "admin/safe_detail_view.html"
    # simple_list_pager = True

    column_exclude_list = ["extra_data", "created_at"]
    list_template = "admin/safe_model_list_view.html"

    def is_accessible(self):
        res = current_user.is_authenticated
        return res

    def __init__(
        self,
        model,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        static_folder=None,
        menu_class_name=None,
        menu_icon_type=None,
        menu_icon_value=None,
    ):
        default_filters = [
            name
            for name, field_type in model._fields.items()
            if not isinstance(field_type, (DictField, ListField, ObjectIdField))
        ]
        object_id_fields = [
            name
            for name, field_type in model._fields.items()
            if isinstance(field_type, (ObjectIdField))
        ]
        for field in object_id_fields:
            default_filters.append(
                ReferenceObjectIdFilter(column=getattr(model, field), name=field)
            )

        list_fields = [
            name
            for name, field_type in model._fields.items()
            if isinstance(field_type, (ListField))
        ]
        for field in list_fields:
            default_filters.append(
                FilterNotInList(column=getattr(model, field), name=field)
            )
            default_filters.append(
                FilterInList(column=getattr(model, field), name=field)
            )

        if not self.column_filters:
            self.column_filters = default_filters
        else:
            self.column_filters = list(self.column_filters) + default_filters

        super().__init__(
            model,
            name,
            category,
            endpoint,
            url,
            static_folder,
            menu_class_name,
            menu_icon_type,
            menu_icon_value,
        )

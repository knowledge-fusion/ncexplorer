import datetime
import json

from mongoengine import StringField

from app.common.mongoengine_base import BaseDocument


class SystemConfig(BaseDocument):
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    key = StringField()
    value = StringField()

    def __unicode__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_or_create_timestamp_value(cls, key, default=datetime.datetime.min):
        """
        get a timestamp object, if not exist, create an object with default value
        :param default:
        :return: datetime object
        """
        setting = cls.objects(key=key).first()
        if setting:
            res = datetime.datetime.strptime(setting.value, cls.DATE_FORMAT)
        else:
            res = default
            value = (
                "0001-01-01 00:00:00"
                if res == datetime.datetime.min
                else res.strftime(cls.DATE_FORMAT)
            )
            cls(key=key, value=value).save()
        return res

    @classmethod
    def update_timestamp_value(cls, key, val=None):
        """
        :param key: string
        :param val: a timestamp value
        :return:
        """
        if not val:
            val = datetime.datetime.utcnow()
        setting = cls.objects(key=key).first()
        if not setting:
            setting = cls(key=key)
        value = (
            "0001-01-01 00:00:00"
            if val == datetime.datetime.min
            else val.strftime(cls.DATE_FORMAT)
        )

        setting.value = value
        res = setting.save()
        return res

    @classmethod
    def get_or_create_dict_value(cls, key, default=None):
        """
        get a timestamp object, if not exist, create an object with default value
        :param default:
        :return: datetime object
        """
        setting = cls.objects(key=key).first()
        if setting and setting.value:
            res = json.loads(setting.value)
        else:
            if not default:
                default = dict()
            res = default
            value = json.dumps(res)
            cls(key=key, value=value).save()
        return res

    @classmethod
    def update_dict_value(cls, key, val=None):
        """
        :param key: string
        :param val: a timestamp value
        :return:
        """
        if not val:
            val = dict()
        setting = cls.objects(key=key).first()
        if not setting:
            setting = cls(key=key)

        setting.value = json.dumps(val)
        res = setting.save()
        return res

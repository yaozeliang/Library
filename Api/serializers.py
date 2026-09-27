from django.contrib.auth.models import Group, User
from rest_framework import serializers

from book.models import Book, Category, Member, Publisher


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


def _required_name():
    """Name is the identity of the row.

    Category.name and Publisher.name are ``blank=True`` on the model, so a
    ModelSerializer would accept a missing, empty, or whitespace-only name
    and store ``""``. The API treats that name as required. Neither field
    is unique, so a repeated name is still a valid create.
    """
    return {"required": True, "allow_blank": False}


# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        extra_kwargs = {"name": _required_name()}

    def to_representation(self, instance):
        representation = super(CategorySerializer, self).to_representation(instance)
        representation["created_at"] = instance.created_at.strftime("%Y/%m/%d")
        return representation


# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "id",
            "author",
            "title",
            "description",
            "quantity",
            "category",
            "publisher",
            "floor_number",
            "bookshelf_number",
        )

    def to_representation(self, instance):
        representation = super(BookSerializer, self).to_representation(instance)
        representation["created_at"] = instance.created_at.strftime("%Y/%m/%d")
        representation["updated_at"] = instance.updated_at.strftime("%Y/%m/%d")

        return representation


# Publisher Serializer
class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = (
            "id",
            "name",
            "city",
            "contact",
        )
        extra_kwargs = {"name": _required_name()}

    def to_representation(self, instance):
        representation = super(PublisherSerializer, self).to_representation(instance)
        representation["created_at"] = instance.created_at.strftime("%Y/%m/%d")
        representation["updated_at"] = instance.updated_at.strftime("%Y/%m/%d")

        return representation


# Membership Serializer
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = (
            "id",
            "name",
            "gender",
            "age",
            "email",
            "city",
            "phone_number",
        )

    def to_representation(self, instance):
        representation = super(MemberSerializer, self).to_representation(instance)
        representation["created_at"] = instance.created_at.strftime("%Y/%m/%d")
        representation["updated_at"] = instance.updated_at.strftime("%Y/%m/%d")

        return representation

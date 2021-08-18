from django.contrib.auth.models import User, Group
from rest_framework import serializers
from book.models import Member,Category,Publisher,Book



class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields="__all__"

    def to_representation(self, instance):
        representation = super(CategorySerializer, self).to_representation(instance)
        representation['created_at'] = instance.created_at.strftime("%Y/%m/%d")
        return representation


# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model=Book
        fields = ('id',
                  'author',
                  'title',
                  'description',
                  'quantity', 
                  'category',
                  'publisher',
                  'floor_number',
                  "bookshelf_number")

    def to_representation(self, instance):
        representation = super(BookSerializer, self).to_representation(instance)
        representation['created_at'] = instance.created_at.strftime("%Y/%m/%d")
        representation['updated_at'] = instance.updated_at.strftime("%Y/%m/%d")

        return representation


# Publisher Serializer
class PublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model=Publisher
        fields = ('id',
                  'name',
                  'city',
                  'contact',
                  )

    def to_representation(self, instance):
        representation = super(PublisherSerializer, self).to_representation(instance)
        representation['created_at'] = instance.created_at.strftime("%Y/%m/%d")
        representation['updated_at'] = instance.updated_at.strftime("%Y/%m/%d")

        return representation



# Membership Serializer
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model=Member
        fields = ("id",
                  'name',
                  'gender',
                  'age',
                  'email',
                  'city', 
                  'phone_number',)

    def to_representation(self, instance):
        representation = super(MemberSerializer, self).to_representation(instance)
        representation['created_at'] = instance.created_at.strftime("%Y/%m/%d")
        representation['updated_at'] = instance.updated_at.strftime("%Y/%m/%d")

        return representation
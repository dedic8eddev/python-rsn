from rest_framework import permissions
from web.models import Comment
from web.constants import UserTypeE


class PostOwnerCanDeleteCommentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Comment):
            if request.user == obj.author:
                return True
            elif obj.post and obj.post.author == request.user:
                return True


class StaffUserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        print(request.user.is_authenticated)
        if request.user.is_authenticated and request.user.type in [UserTypeE.EDITOR, UserTypeE.ADMINISTRATOR]:
            return True

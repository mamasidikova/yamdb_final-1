from django.db.models import Avg
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, mixins, permissions, response, status,
                            viewsets)
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Review, Title, User

from . import serializers
from .filters import TitleFilter
from .permissions import (IsAdminOrReadOnly, IsAuthorOrReadOnly,
                          IsModeratorOrReadOnly, IsOwnerOrIsAdmin)
from .utils import code_gen, send_email


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = [IsAdminOrReadOnly]


@api_view(['POST'])
def register_view(request):
    serializer = serializers.RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data.get('email')
    username = serializer.validated_data.get('username')
    users = User.objects.filter(email__iexact=email, username=username)
    user = users.first()

    if user is None:
        email_users = User.objects.filter(email__iexact=email)
        email_user = email_users.first()
        name_users = User.objects.filter(username=username)
        name_user = name_users.first()
        if (email_user is not None or name_user is not None):
            return Response(
                ('Аккаунт с таким именем пользователя '
                 'или почтой уже существует!'),
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.create_user(
            **serializer.validated_data
        )
    else:
        user = User.objects.get(email__iexact=email, username=username)
    confirmation_code = code_gen()
    user.confirmation_code = confirmation_code
    user.save()
    send_email(username, email, confirmation_code)
    return Response(
        serializer.validated_data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def token_view(request):
    serializer = serializers.TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        username=serializer.validated_data.get('username')
    )
    confirmation_code = user.confirmation_code
    input_confirmation_code = serializer.validated_data.get(
        'confirmation_code'
    )
    if input_confirmation_code == confirmation_code:
        token = AccessToken.for_user(user)
        return Response({'Token': str(token)}, status.HTTP_200_OK)
    return Response('Код подтверждения неверный!',
                    status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = 'username'
    permission_classes = [IsOwnerOrIsAdmin]

    @action(
        detail=False,
        url_path="me",
        methods=['GET', 'PATCH'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_self_user_page(self, request):
        if request.method == 'GET':
            serializer = serializers.UserSerializer(request.user)
            return response.Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        serializer = serializers.UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role, partial=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = serializers.GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).order_by('-year')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return serializers.TitleCreateSerializer
        return serializers.TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [IsAuthorOrReadOnly | IsModeratorOrReadOnly]

    def _get_title(self):
        return get_object_or_404(Title, pk=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self._get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self._get_title())


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthorOrReadOnly | IsModeratorOrReadOnly]

    def _get_review(self):
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'))

    def get_queryset(self):
        return self._get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self._get_review())

# posts/tests/test_urls.py
from django.test import TestCase, Client
from django.core.cache import cache
from django.contrib.auth import get_user_model
from http import HTTPStatus
from posts.models import Group, Post, Comment

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_templates_urls(self):
        pages = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        for url, template in pages.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_non_auth_pages(self):
        non_auth_pages = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        ]

        for pages in non_auth_pages:
            response = self.guest_client.get(pages)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_page(self):
        """Страницы доступны только авторизированному пользователю."""
        auth_pages = [
            '/create/',
            '/follow/',
        ]

        for pages in auth_pages:
            response = self.authorized_client.get(pages)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_page_redirect(self):
        """Страницы доступны только авторизированному пользователю."""
        auth_pages = [
            
            f'/profile/{self.user.username}/follow',
            f'/profile/{self.user.username}/unfollow'
        ]

        for pages in auth_pages:
            response = self.authorized_client.get(pages)
            self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_comment_page(self):
        """Проверка страницы comment."""
        page = f'/posts/{self.post.id}/comment/'
        response = self.authorized_client.get(page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_page(self):
        """Страница /edit/ доступна только автору поста."""
        other_user = User.objects.create_user(username='OtherTestUser')
        other_post = Post.objects.create(
            author=other_user,
            text='Другой пост пользователя'
        )

        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.authorized_client.get(f'/posts/{other_post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comment_page(self):
        """Страница /comment/ доступна авторизированному пользователю."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/comment')
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_nonexistent_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.client.get('/nonexistent_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')

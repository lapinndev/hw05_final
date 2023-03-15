import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django import forms

from posts.models import Group, Post, Follow


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group1 = Group.objects.create(
            title='Група 1',
            slug='test-slug-1',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context['page_obj'][0]
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.group)
        self.assertEqual(context.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        context = response.context['page_obj'][0]
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.group)
        self.assertEqual(context.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        context = response.context['page_obj'][0]
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.group)
        self.assertEqual(context.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        context = response.context['post']
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.group)
        self.assertEqual(context.image, self.post.image)

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appear_on_correct_pages(self):
        response_index = self.client.get(reverse('posts:index'))
        response_group1 = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group1.slug}))
        response_group = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        response_user = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))

        self.assertIn(self.post, response_index.context['page_obj'])
        self.assertIn(self.post, response_group.context['page_obj'])
        self.assertIn(self.post, response_user.context['page_obj'])
        self.assertNotIn(self.post, response_group1.context['page_obj'])

    def test_cache_index(self):
        first_response = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(id=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_response.content, third_response.content)


class FollowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('Follow')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow(self):
        """Пользователь может подписываться на других пользователей."""
        author_user = User.objects.create_user(username='author_user')
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=(author_user.username,)))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=author_user
                                             ).exists()
        self.assertTrue(follow_exist)

    def test_unfollow(self):
        """Пользователь может отписываться от других пользователей."""
        author_user = User.objects.create_user(username='author_user')
        Follow.objects.create(user=self.user,
                              author=author_user)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            args=(author_user.username,)))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=author_user
                                             ).exists()
        self.assertFalse(follow_exist)

    def test_check_posts_in_follow_index(self):
        """Посты избранных авторов выводятся в follow_index."""
        author_user = User.objects.create_user(username='author_user')
        post = Post.objects.create(
            text='текстовый пост для проверки follow_index',
            author=author_user
        )
        Follow.objects.create(
            user=self.user,
            author=author_user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])

    def test_check_posts_not_in_follow(self):
        """Посты не избранных авторов не выводятся в follow_index."""
        author_user = User.objects.create_user(username='author_user')
        post = Post.objects.create(
            text='текстовый пост для проверки follow_index',
            author=author_user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])

    def test_not_follow_user_user(self):
        """Пользователь не может подписаться сам на себя."""
        author_user = User.objects.create_user(username='author_user')
        self.authorized_client.force_login(author_user)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=(author_user.username,)))
        follow_exist = Follow.objects.filter(user=author_user,
                                             author=author_user).exists()
        self.assertFalse(follow_exist)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.user = User.objects.create_user(username='TestUser')
        posts = [Post(text=f'Тестовый пост {i}',
                      author=cls.user, group=cls.group) for i in range(13)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_index_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_list_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

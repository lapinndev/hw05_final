from django.contrib.auth import get_user_model
from django.test import TestCase


from posts.models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Неосмысленная жизнь не стоит того, чтобы жить.',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий для проверки.'
        )

    def test_models_post_have_correct_object_names(self):
        """Проверяем, что у модели post корректно работает __str__."""
        post = PostModelTest.post

        self.assertEqual(str(post), post.text[:15])

    def test_models_group_have_correct_object_names(self):
        """Проверяем, что у модели group корректно работает __str__."""
        group = PostModelTest.group

        self.assertEqual(str(group), group.title)

    def test_models_comment_have_correct_object_names(self):
        """Проверяем, что у модели comment корректно работает __str__."""
        comment = PostModelTest.comment

        self.assertEqual(str(comment), comment.text)

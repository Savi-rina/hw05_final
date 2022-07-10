import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

POSTS_PER_PAGE = 10
POSTS_LEFT_ON_PAGE = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    """Тестируем views"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(name='small.gif', content=small_gif,
                                      content_type='image/gif')

        cls.user = User.objects.create_user(username='Marina')
        cls.author = User.objects.create_user(username='Irina')
        cls.group = Group.objects.create(slug='test-slug',
                                         description='Тестовое описание',
                                         title='Тестовый заголовок',
                                         )
        cls.group_2 = Group.objects.create(slug='test-slug2',
                                           description='Тестовое описание2',
                                           title='Тестовый заголовок2', )
        cls.post = Post.objects.create(author=cls.author, text='Тестовый пост',
                                       group=cls.group, image=uploaded)

        cls.comment = Comment.objects.create(author=cls.author,
                                             text='Тестовый комментарий')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_refers_to_correct_template_for_all(self):
        """URL-адрес использует соответствующий шаблон для всех пользователей.
        """
        templates_pages_names = {'posts/index.html': reverse('posts:index'),
                                 'posts/group_list.html': reverse(
                                     'posts:group_list',
                                     kwargs={'slug': self.group.slug}),
                                 'posts/profile.html': reverse(
                                     'posts:profile',
                                     kwargs={'username': self.author}),
                                 'posts/post_detail.html': reverse(
                                     'posts:post_detail',
                                     kwargs={'post_id': self.post.id})}

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_post_all_atributes(self, post):
        self.assertEqual(post.group.title, self.post.group.title)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.id, self.post.id)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))

        self.check_post_all_atributes(response.context['page_obj'][0])

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))

        self.assertEqual(response.context.get('group'), self.group)
        self.check_post_all_atributes(response.context['page_obj'][0])

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))

        self.assertEqual(response.context.get('author'), self.post.author)
        self.check_post_all_atributes(response.context['page_obj'][0])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контестом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        first_post = response.context['post']
        post_text = first_post.text
        post_id = first_post.id
        post_author = first_post.author
        post_group = first_post.group

        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_id, self.post.id)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_group, self.group)

    def test_check_post_is_on_all_realted_pages(self):
        """Пост появлятеся на главной странице, странице выбранной группы
        и в профайле.
        """
        pages = {reverse('posts:index'),
                 reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                 reverse('posts:profile', kwargs={'username': self.author})}
        for address in pages:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.context.get('page_obj')[0],
                                 self.post)

    def test_post_is_in_correct_group(self):
        """Пост при создании не попадает в другую группу"""
        response = self.client.get(
            reverse("posts:group_list", args=[self.group_2.slug]))
        self.assertEqual(len(response.context.get('page_obj').object_list), 0)

    def test_pages_refers_to_correct_template_for_authorized(self):
        """URL-адрес использует соответствующий шаблон
         для авторизованных пользователей.
         """
        response = self.authorized_user.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = (self.authorized_user.get(reverse('posts:post_create')))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context_for_post_edit(self):
        """Шаблон create_post сформирован с правильным контекстом
        при редактировании поста."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context['is_edit'], True)
        self.assertIsInstance(response.context['is_edit'], bool)

    def test_pages_refers_to_correct_template_for_author(self):
        """URL-адрес использует соответствующий шаблон для автора."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_only_authorized_user_can_add_comment(self):
        """Только авторизованный пользователь может комментировать посты."""
        self.author_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}))

        self.assertTrue(Comment.objects.filter(text='Тестовый комментарий',
                                               author=self.author).exists())

    def test_cache_for_index(self):
        """Проверка работы кеша для главной страницы."""
        post = Post.objects.create(author=self.author, text='какой-то текст')

        posts = (self.author_client.get(reverse('posts:index'))).content

        post.delete()

        posts_cache = (self.author_client.get(reverse('posts:index'))).content

        cache.clear()

        posts_updated = (
            self.author_client.get(reverse('posts:index'))).content

        self.assertEqual(posts, posts_cache)
        self.assertNotEqual(posts_cache, posts_updated)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug',
                                         description='Тестовое описание', )

        for post in range(sum([POSTS_PER_PAGE, POSTS_LEFT_ON_PAGE])):
            Post.objects.create(text=f'Тестовый текст {post}', author=cls.user,
                                group=cls.group, )

    def test_first_page_contains_ten_posts(self):
        """Первая страница содержит десять постов."""
        pages_with_pagination = [reverse('posts:index'),
                                 reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}),
                                 reverse('posts:profile',
                                         kwargs={'username': self.user}), ]
        for address in pages_with_pagination:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_PER_PAGE)

    def test_second_page_contains_three_posts(self):
        """Вторая страница содердит три поста."""
        pages_with_pagination = [reverse('posts:index') + '?page=2',
                                 reverse('posts:group_list', kwargs={
                                     'slug': self.group.slug}) + '?page=2',
                                 reverse('posts:profile', kwargs={
                                     'username': self.user}) + '?page=2', ]
        for address in pages_with_pagination:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_LEFT_ON_PAGE)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Marina')
        cls.author = User.objects.create_user(username='Irina')
        cls.post = Post.objects.create(author=cls.author, text='Тестовый пост')

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_authorized_can_follow_other_users(self):
        """Авторизованный пользователь может подписываться на других
        пользователей.
        """

        follow_count = Follow.objects.count()

        self.authorized_user.post(reverse('posts:profile_follow', kwargs={
            'username': f'{self.author.username}'}))

        self.assertEqual(Follow.objects.count(), follow_count + 1)

        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists())

    def test_guest_can_not_follow_other_users(self):
        """Неавторизованный пользователь не может подписываться на других
        пользователей.
        """
        follow_count = Follow.objects.count()

        self.client.post(reverse('posts:profile_follow', kwargs={
            'username': f'{self.author.username}'}))

        self.assertEqual(Follow.objects.count(), follow_count)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может удалять
        других пользователей из подписок.
        """
        self.authorized_user.post(reverse('posts:profile_follow', kwargs={
            'username': f'{self.author.username}'}))

        follow = Follow.objects.filter(user=self.user, author=self.author)

        follow_count = Follow.objects.count()

        follow.delete()

        self.assertNotEqual(Follow.objects.count(), follow_count)

    def test_new_post_appears_for_followers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """

        Follow.objects.create(user=self.user, author=self.author)

        Post.objects.create(text='Какой-то текст', author=self.author)

        self.authorized_user.get(reverse('posts:follow_index'))

        self.assertTrue(Post.objects.filter(text='Какой-то текст',
                                            author=self.author).exists())

    def test_new_post_does_not_appear_for_non_followers(self):
        """Новая запись пользователя не появляется в ленте тех, кто не подписан.
        """
        Post.objects.create(text='Какой-то текст', author=self.author)

        response = self.authorized_user.get(reverse('posts:follow_index'))

        self.assertEqual(len(response.context.get('page_obj').object_list), 0)

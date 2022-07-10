from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsUrlTests(TestCase):
    """Тестируем urls"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        # Создаем пользователя
        self.user_2 = User.objects.create_user(username='HasNoName')
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user_2)
        # Создаем клиент и логиним автора
        self.post_author = Client()
        self.post_author.force_login(self.user)

        cache.clear()

    def test_unexisting_page(self):
        """Страница unexisting_page вернет ошибку 404"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_refers_to_correct_template_for_all(self):
        """ Для каждого URL-адреса возвращается
        правильный шаблон для всех пользователей.
        """
        templates_and_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
        }
        for template, address in templates_and_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_refers_to_correct_template_for_authorized(self):
        """ Для URL-адреса создания поста возращается
        правильный шаблон для авторизованного пользователя.
        """
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_url_refers_to_correct_template_for_author(self):
        """ Для URL-адреса редактирования поста возращается
        правильный шаблон для автора.
        """
        response = self.post_author.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_url_is_available_for_all(self):
        """Главная страница доступна любому пользователю."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_list_url_is_available_for_all(self):
        """Страница с постами, отфильтрованными по группе,
        доступна любому пользователю.
        """
        response = self.client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_author_profile_url_is_available_for_all(self):
        """Страница с профайлом доступна любому пользователю."""
        response = self.client.get(f'/profile/{self.user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail_url_is_available_for_all(self):
        """Страница с деталями поста доступна любому пользователю."""
        response = self.client.get(f'/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_post_create_url_is_available_for_authorized(self):
        """Post_create доступна авторизованным пользователям."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_is_available_for_author_only(self):
        """Страница /posts/<post_id>/edit доступна только автору"""
        response = self.post_author.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_create_post_url_redirect_guest(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_url_redirect_guest(self):
        """Страница /posts/<post_id>/edit перенаправляет анонимного
        пользователя.
        """
        response = self.client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_not_author_wants_edit_post(self):
        """Не автор пытается редактировать пост."""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_create_post_url_guest_user(self):
        """Гость не должен иметь доступ к странице
        создания поста."""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_edit_post_url_guest_user(self):
        """Гость не должен иметь доступ к странице
        редактирования поста."""
        response = self.client.get(f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.pk}/edit/'))

    def test_edit_post_url_not_author(self):
        """Не автор при попытке редактирования
         перенаправляется на post_detail."""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/',
                                              follow=True)

        self.assertRedirects(response, f'/posts/{self.post.pk}/')

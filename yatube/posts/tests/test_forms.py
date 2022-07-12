from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Marina')
        cls.author = User.objects.create_user(username='Irina')
        cls.group = Group.objects.create(title='Тестовый заголовок',
                                         slug='test_slug',
                                         description='Тестовое описание')
        cls.post = Post.objects.create(author=cls.author, text='Тестовый пост',
                                       group=cls.group)

        cls.comment = Comment.objects.create(author=cls.author,
                                             text='Тестовый комментарий')

        cls.form = PostForm()

        cls.gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                   b'\x01\x00\x80\x00\x00\x00\x00\x00'
                   b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                   b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                   b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                   b'\x0A\x00\x3B')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def check_post_all_atributes(self, test_post, form_data):
        self.assertEqual(test_post.author, self.post.author)
        self.assertEqual(test_post.group.id, form_data['group'])
        self.assertEqual(test_post.text, form_data['text'])

    def test_authorized_client_can_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = self.gif
        uploaded = SimpleUploadedFile(name='small.gif', content=small_gif,
                                      content_type='image/gif')
        form_data = {'text': 'текст поста', 'group': self.group.id,
                     'image': uploaded}

        response = self.author_client.post(reverse('posts:post_create'),
                                           data=form_data, follow=True)
        test_post = Post.objects.first()

        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.author}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.check_post_all_atributes(test_post, form_data)
        self.assertEqual(test_post.image.read(), self.gif)

    def test_cannot_create_post_without_text(self):
        """Проверяем, что пост не может создаться без текста.
        Для этого подсчитаем количество записей в Post,
        убедимся, что запись в базе данных не создалась,
        сравним количество записей в Post до и после отправки формы
        и проверим, что ничего не упало и страница отдаёт код 200.
        """
        posts_count = Post.objects.count()
        form_data = {'text': ''}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_only_author_can_edit_post(self):
        """Валидная форма редактирует запись в Post.
        Подсчитаем количество записей в Post,
        отправляем POST-запрос,проверяем, сработал ли редирект,
        проверяем, не увеличилось ли число постов,
        проверяем, что запись с заданным id отредактировалась.
        """
        posts_count = Post.objects.count()
        form_data = {'text': 'Отредактированный пост', 'group': self.group.id}
        response = self.author_client.post(
            reverse(('posts:post_edit'),
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data, follow=True)

        test_post = Post.objects.get(id=self.post.id)

        self.assertRedirects(response, reverse(('posts:post_detail'), kwargs={
            'post_id': f'{self.post.id}'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.check_post_all_atributes(test_post, form_data)

    def test_cannot_edit_post_without_text(self):
        posts_count = Post.objects.count()
        form_data = {'text': ''}
        response = self.author_client.post(reverse(('posts:post_edit'),
                                                   kwargs={
                                                       'post_id':
                                                           f'{self.post.id}'}),
                                           data=form_data, follow=True)

        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_only_authorized_client_can_add_comment(self):
        """Только авторизованный пользователь может комментировать посты.
        После успешной отправки комментарий появляется на странице поста.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий к посту',
        }
        response = self.authorized_client.post(
            reverse((
                'posts:add_comment'),
                kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse((
            'posts:post_detail'), kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.first().text, form_data['text'])
        self.assertEqual(Comment.objects.first().author, self.user)

    def test_guest_can_not_add_comment(self):
        """Гость не может комментировать посты."""

        response = self.client.post(
            reverse((
                'posts:add_comment'),
                kwargs={'post_id': f'{self.post.id}'}),
            follow=True,
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/'
                             f'{self.post.id}/comment/')

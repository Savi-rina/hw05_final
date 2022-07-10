from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

MAX_LETTERS = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 10
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__,
        т.е возвращает текст поста и название группы.
        Через str() получаем строковое представление объекта модели.
        Схема ассерта:call, result,текст ошибки.Проверяем call==result или нет.
        Конструкция for model, expected_value in models_strings.items()
        распаковывает словарь models_strings с помощью метода items() —
        создаёт из него два кортежа, доступных для итерации с помощью цикла

        Кортеж model содержит ключи словаря models_strings;
        Кортеж expected_value содержит значения словаря models_strings;

        Значения из кортежа model передаются
        как параметр в self.subTest(model=model).
        """
        models_strings = {
            self.post: self.post.text[:MAX_LETTERS],
            self.group: self.group.title,
        }

        for model, expected_values in models_strings.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_values,
                                 'Ошибка метода str(): текст не возвращается',
                                 )

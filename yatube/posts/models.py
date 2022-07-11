from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

MAX_LETTERS = 15


class Group(models.Model):
    """Содаем модель Group, наследник класса Model из пакета models.
    Описываем поля модели и их типы."""

    title = models.CharField(max_length=200, verbose_name='Название группы')
    slug = models.SlugField(unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        """Выводит строковое представление объекта данного класса."""
        return self.title


class Post(models.Model):
    """Содаем модель Post, наследник класса Model из пакета models.

    Описываем поля модели и их типы.Свойства имя_свойства = models.тип_данных()
    определят названия и типы данных в колонках таблицы БД.

    Для полей в моделях указывают типы данных,
    соответствующие типам данных в БД.

    По имени related_name (в данном случае posts) мы можем получить
    все посты из объекта author
    и в нём будут храниться ссылки на все объекты модели Post,
    которые ссылаются на объект User.
    """

    text = models.TextField(verbose_name='Пост',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )

    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Посты группы',
        help_text='Выберите группу',
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        """Возравращает текст поста."""
        return self.text[:MAX_LETTERS]


class Comment(models.Model):
    """Содаем модель Comment, наследник класса Model из пакета models."""

    post = models.ForeignKey(Post, blank=True, null=True,
                             on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Пост')

    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор комменатрия')
    text = models.TextField(verbose_name='Комменатрий',
                            help_text='Напишите комментарий')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата публикации комментария')

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        """Возравращает текст комменатрия."""
        return self.text[:MAX_LETTERS]


class Follow(models.Model):
    """Содаем модель Follow, наследник класса Model из пакета models."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following', verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'

        constraints = [models.UniqueConstraint(fields=('user', 'author'),
                                               name='unique_follow')]

    def __str__(self):
        return str(self.user)

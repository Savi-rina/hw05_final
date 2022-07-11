from django.contrib import admin

from .models import Group, Post, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    """
    Адиминистрируем модель Post, источником конфигурации для неё назначаем
    класс PostAdmin.

    Для настройки отображения модели в интерфейсе админки применяют
    класс ModelAdmin.

    Attributes:
        list_display: tuple - кортеж полей, отображаемых в админке.
        list_editable: tuple - кортеж полей для редактирования,
        отображаемых в админке.
        search_fields: tuple - перечень полей,
        по которым будет искать поисковая система.
        list_filter: tuple - перечень полей,по которым можно фильтровать записи
        empty_value_display: str - дефолтное значение вместо пустого поля.
    """

    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment)
admin.site.register(Follow)

from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Создаем класс формы с заданными полями, которые мы в нее передадим."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Создаем класс формы комментария."""
    class Meta:
        model = Comment
        fields = ('text',)

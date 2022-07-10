from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(UserCreationForm):
    """Создаем собственный класс для формы регистрации.

    Сделаем его наследником предустановленного класса UserCreationForm.
    """

    class Meta(UserCreationForm.Meta):

        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

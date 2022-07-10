from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Класс для отображения статичной страницы об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Класс для отображения статичной страницы о технологиях."""
    template_name = 'about/tech.html'

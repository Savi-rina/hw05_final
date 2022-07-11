from django.test import TestCase


class ViewTestClass(TestCase):

    def test_unexisting_page_refers_to_correct_template(self):
        """ Cтраница 404 отдает кастомный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

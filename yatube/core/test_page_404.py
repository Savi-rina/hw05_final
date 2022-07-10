from django.test import Client, TestCase


class ViewTestClass(TestCase):

    def setUp(self):
        self.client = Client()

    def test_unexisting_page_refers_to_correct_template(self):
        """ Cтраница 404 отдает кастомный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

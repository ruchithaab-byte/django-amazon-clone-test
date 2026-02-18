from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from DjangoEcommerceApp.models import Categories

class CategoryListTemplateTest(TestCase):
    def setUp(self):
        # Create a test admin user
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@example.com',
            password='testpassword123'
        )

        # Create some test categories
        Categories.objects.create(
            title='Test Category 1',
            description='Description 1',
            url_slug='test-category-1',
            is_active=1,
            thumbnail=None
        )
        Categories.objects.create(
            title='Test Category 2',
            description='Description 2',
            url_slug='test-category-2',
            is_active=0,
            thumbnail=None
        )

    def test_category_list_template_rendering(self):
        # Log in the admin user
        self.client.login(username='testadmin', password='testpassword123')

        # Get the category list page
        response = self.client.get(reverse('category_list'))

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check template used
        self.assertTemplateUsed(response, 'admin_templates/category_list.html')

        # Check context variables
        self.assertIn('categories_list', response.context)
        self.assertEqual(len(response.context['categories_list']), 2)

        # Check specific content
        self.assertContains(response, 'Test Category 1')
        self.assertContains(response, 'Test Category 2')

    def test_category_list_pagination(self):
        # Log in the admin user
        self.client.login(username='testadmin', password='testpassword123')

        # Create more categories to test pagination
        for i in range(3, 15):
            Categories.objects.create(
                title=f'Test Category {i}',
                description=f'Description {i}',
                url_slug=f'test-category-{i}',
                is_active=1,
                thumbnail=None
            )

        # Get the category list page
        response = self.client.get(reverse('category_list'))

        # Check pagination
        self.assertIn('page_obj', response.context)
        self.assertIn('paginator', response.context)
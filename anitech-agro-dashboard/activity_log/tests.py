from django.test import RequestFactory, SimpleTestCase

from .middleware import ActivityLogMiddleware


class ActivityLogMiddlewareTest(SimpleTestCase):
    def setUp(self):
        self.middleware = ActivityLogMiddleware(lambda request: None)
        self.factory = RequestFactory()

    def test_read_actions_use_specific_page_labels(self):
        request = self.factory.get('/notifications/')

        action = self.middleware._get_action_description(request, 'read', 'notification')

        self.assertEqual(action, 'Viewed notifications')

    def test_post_edit_paths_are_treated_as_updates(self):
        request = self.factory.post('/inventory/4/edit/', {
            'crop_name': 'Rice',
            'current_price': '52.00',
        })

        event_type = self.middleware._get_event_type(request, type('Response', (), {'status_code': 302})())
        action = self.middleware._get_action_description(request, event_type, 'inventory')

        self.assertEqual(event_type, 'update')
        self.assertEqual(action, 'Updated Inventory')

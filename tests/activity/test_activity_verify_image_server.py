import unittest
import settings_mock
from activity.activity_VerifyImageServer import activity_VerifyImageServer
import test_activity_data as test_data
from mock import patch, MagicMock
from classes_mock import FakeSession
from classes_mock import FakeStorageContext
from ddt import ddt, data

class FakeStorageContext:
    def list_resources(self, resource):
        return ['elife-003530-fig1-v1-1022w.jpg',
                'elife-003530-fig1-v1-80w.jpg',
                'elife-003530-fig1-v1-1022w.gif',
                'elife-003530-fig1-v1.jpg',
                'elife-003530-fig1-v1.tif',
                'elife-003530-fig1-v1-download.jpg',
                'elife-003530-fig1-v1-download.xml']


class TestVerifyImageServer(unittest.TestCase):
    def setUp(self):
        self.verifyimageserver = activity_VerifyImageServer(settings_mock, None, None, None, None)



    @patch('activity.activity_VerifyImageServer.StorageContext')
    @patch('activity.activity_VerifyImageServer.Session')
    @patch.object(activity_VerifyImageServer, 'test_iiif_endpoint')
    def test_do_activity_success(self, test_iiif_endpoint_mock, fake_session, fake_storage_context):
        # Given
        data = test_data.data_example_before_publish
        test_iiif_endpoint_mock.return_value = True, "test.path"
        fake_session.return_value = FakeSession(test_data.session_example)
        fake_storage_context.return_value = FakeStorageContext()
        self.verifyimageserver.emit_monitor_event = MagicMock()
        self.verifyimageserver.logger = MagicMock()
        # When
        result = self.verifyimageserver.do_activity(data)
        # Then
        self.assertEqual(result, self.verifyimageserver.ACTIVITY_SUCCESS)

    @patch('activity.activity_VerifyImageServer.StorageContext')
    @patch('activity.activity_VerifyImageServer.Session')
    @patch.object(activity_VerifyImageServer, 'test_iiif_endpoint')
    def test_do_activity_failure(self, test_iiif_endpoint_mock, fake_session, fake_storage_context):
        # Given
        data = test_data.data_example_before_publish
        test_iiif_endpoint_mock.return_value = False, "test.path"
        fake_session.return_value = FakeSession(test_data.session_example)
        fake_storage_context.return_value = FakeStorageContext()
        self.verifyimageserver.emit_monitor_event = MagicMock()
        self.verifyimageserver.logger = MagicMock()
        # When
        result = self.verifyimageserver.do_activity(data)
        # Then
        self.assertEqual(result, self.verifyimageserver.ACTIVITY_PERMANENT_FAILURE)

    @patch('activity.activity_VerifyImageServer.StorageContext')
    @patch('activity.activity_VerifyImageServer.Session')
    @patch.object(activity_VerifyImageServer, 'test_iiif_endpoint')
    def test_do_activity_error(self, test_iiif_endpoint_mock, fake_session, fake_storage_context):
        # Given
        data = test_data.data_example_before_publish
        test_iiif_endpoint_mock.side_effect = Exception("Error!")
        fake_session.return_value = FakeSession(test_data.session_example)
        fake_storage_context.return_value = FakeStorageContext()
        self.verifyimageserver.emit_monitor_event = MagicMock()
        self.verifyimageserver.logger = MagicMock()
        # When
        result = self.verifyimageserver.do_activity(data)
        # Then
        self.assertEqual(result, self.verifyimageserver.ACTIVITY_PERMANENT_FAILURE)


if __name__ == '__main__':
    unittest.main()

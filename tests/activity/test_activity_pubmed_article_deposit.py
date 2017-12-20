import unittest
from activity.activity_PubmedArticleDeposit import activity_PubmedArticleDeposit
import shutil
from mock import patch
import tests.activity.settings_mock as settings_mock
from tests.activity.classes_mock import FakeLogger
from provider.article import article
from provider.simpleDB import SimpleDB
from provider import lax_provider
import tests.test_data as test_case_data
import os
from ddt import ddt, data
from classes_mock import FakeStorageContext


@ddt
class TestPubmedArticleDeposit(unittest.TestCase):

    def setUp(self):
        fake_logger = FakeLogger()
        self.activity = activity_PubmedArticleDeposit(settings_mock, fake_logger, None, None, None)


    def tearDown(self):
        self.activity.clean_tmp_dir()


    def input_dir(self):
        "return the staging dir name for the activity"
        return os.path.join(self.activity.get_tmp_dir(), self.activity.INPUT_DIR)


    def tmp_dir(self):
        "return the tmp dir name for the activity"
        return os.path.join(self.activity.get_tmp_dir(), self.activity.TMP_DIR)


    @patch.object(SimpleDB, 'elife_add_email_to_email_queue')
    @patch.object(lax_provider, 'article_versions')
    @patch.object(activity_PubmedArticleDeposit, 'upload_pubmed_xml_to_s3')
    @patch.object(activity_PubmedArticleDeposit, 'ftp_files_to_endpoint')
    @patch('activity.activity_PubmedArticleDeposit.storage_context')
    @patch.object(FakeStorageContext, 'list_resources')
    @data(
        {
            "comment": 'example PoA file will have an aheadofprint',
            "outbox_filenames": ['elife-29353-v1.xml', 'not_an_xml_file.pdf'],
            "ftp_files_return_value": True,
            "article_versions_data": test_case_data.lax_article_versions_response_data,
            "expected_result": True,
            "expected_approve_status": True,
            "expected_generate_status": True,
            "expected_publish_status": True,
            "expected_ftp_status": True,
            "expected_activity_status": True,
            "expected_file_count": 1,
            "expected_pubmed_xml_contains": [
                '<ArticleTitle>An evolutionary young defense metabolite influences the root growth of plants via the ancient TOR signaling pathway</ArticleTitle>',
                '<PubDate PubStatus="aheadofprint"><Year>2017</Year><Month>December</Month><Day>12</Day></PubDate>',
                '<ELocationID EIdType="doi">10.7554/eLife.29353</ELocationID>'
                ]
        },
        {
            "comment": 'example VoR file will have a Replaces tag',
            "outbox_filenames": ['elife-15747-v2.xml'],
            "ftp_files_return_value": True,
            "article_versions_data": test_case_data.lax_article_versions_response_data,
            "expected_result": True,
            "expected_approve_status": True,
            "expected_generate_status": True,
            "expected_publish_status": True,
            "expected_ftp_status": True,
            "expected_activity_status": True,
            "expected_file_count": 1,
            "expected_pubmed_xml_contains": [
                '<Replaces IdType="doi">10.7554/eLife.15747</Replaces>',
                '<ArticleTitle>Community-level cohesion without cooperation</ArticleTitle>',
                '<PubDate PubStatus="epublish"><Year>2016</Year><Month>June</Month><Day>16</Day></PubDate>',
                '<ELocationID EIdType="doi">10.7554/eLife.15747</ELocationID>',
                '<Identifier Source="ORCID">http://orcid.org/0000-0002-9558-1121</Identifier>'
                ]
        },
        {
            "comment": 'test for if the article is published False (not published yet)',
            "outbox_filenames": ['elife-15747-v2.xml'],
            "ftp_files_return_value": True,
            "article_versions_data": [],
            "expected_result": True,
            "expected_approve_status": False,
            "expected_generate_status": False,
            "expected_publish_status": None,
            "expected_ftp_status": None,
            "expected_activity_status": True,
            "expected_file_count": 0
        },
        {
            "comment": 'test for if FTP status is False',
            "outbox_filenames": ['elife-15747-v2.xml'],
            "ftp_files_return_value": False,
            "article_versions_data": test_case_data.lax_article_versions_response_data,
            "expected_result": False,
            "expected_approve_status": True,
            "expected_generate_status": True,
            "expected_publish_status": False,
            "expected_ftp_status": False,
            "expected_activity_status": False,
            "expected_file_count": 1,
        },
        {
            "comment": 'test for if the XML file has no version it will use lax data',
            "outbox_filenames": ['elife-15747.xml'],
            "ftp_files_return_value": True,
            "article_versions_data": test_case_data.lax_article_versions_response_data,
            "expected_result": True,
            "expected_approve_status": True,
            "expected_generate_status": True,
            "expected_publish_status": True,
            "expected_ftp_status": True,
            "expected_activity_status": True,
            "expected_file_count": 1,
            "expected_pubmed_xml_contains": [
                '<Replaces IdType="doi">10.7554/eLife.15747</Replaces>'
                ]
        },
    )
    def test_do_activity(self, test_data, fake_list_resources, fake_storage_context,
                         fake_ftp_files_to_endpoint, fake_upload_pubmed_xml_to_s3,
                         fake_lax_provider_article_versions, fake_elife_add_email_to_email_queue):
        # copy XML files into the input directory using the storage context
        fake_storage_context.return_value = FakeStorageContext()
        fake_list_resources.return_value = test_data.get("outbox_filenames")
        # lax data overrides
        fake_lax_provider_article_versions.return_value = 200, test_data.get("article_versions_data")
        # ftp
        fake_ftp_files_to_endpoint.return_value = test_data.get("ftp_files_return_value")
        # do the activity
        result = self.activity.do_activity()
        # check assertions
        self.assertEqual(result, test_data.get("expected_result"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        self.assertEqual(self.activity.approve_status, test_data.get("expected_approve_status"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        self.assertEqual(self.activity.generate_status, test_data.get("expected_generate_status"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        self.assertEqual(self.activity.publish_status, test_data.get("expected_publish_status"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        self.assertEqual(self.activity.activity_status, test_data.get("expected_activity_status"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        # check the outbox_s3_key_names values
        self.assertEqual(self.activity.outbox_s3_key_names,
                         [self.activity.outbox_folder + '/' + filename
                          for filename in test_data.get("outbox_filenames")],
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        # Count PubMed XML file in the tmp directory
        file_count = len(os.listdir(self.tmp_dir()))
        self.assertEqual(file_count, test_data.get("expected_file_count"),
                         'failed in {comment}'.format(comment=test_data.get("comment")))
        if file_count > 0 and test_data.get("expected_pubmed_xml_contains"):
            # Open the first Pubmed XML and check some of its contents
            pubmed_xml_filename_path = os.path.join(self.tmp_dir(), os.listdir(self.tmp_dir())[0])
            with open(pubmed_xml_filename_path, 'rb') as fp:
                pubmed_xml = fp.read()
                for expected in test_data.get("expected_pubmed_xml_contains"):
                    self.assertTrue(
                        expected in pubmed_xml,
                        'failed in {comment}: {expected} not found in pubmed_xml {path}'.format(
                            comment=test_data.get("comment"), expected=expected,
                            path=pubmed_xml_filename_path))
        # clean directory after each test
        self.activity.clean_tmp_dir()

    @data(
        {
            "article_xml": 'elife-29353-v1.xml',
            "expected_article": "not none",
            "expected_doi": '10.7554/eLife.29353'
        },
        {
            "article_xml": 'bad_xml.xml',
            "expected_article": None
        }
    )
    def test_parse_article_xml(self, test_data):
        source_doc = "tests/files_source/pubmed/outbox/" + test_data.get('article_xml')
        article = self.activity.parse_article_xml(source_doc)
        if test_data.get('expected_article') is None:
            self.assertEqual(article, test_data.get('expected_article'),
                             'failed comparing expected_article')
        else:
            self.assertIsNotNone(article, 'failed comparing expected_article')
        if article:
            self.assertEqual(article.doi, test_data.get('expected_doi'),
                         'failed comparing expected_doi')


if __name__ == '__main__':
    unittest.main()

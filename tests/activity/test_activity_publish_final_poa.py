import unittest
from activity.activity_PublishFinalPOA import activity_PublishFinalPOA
import json
import shutil
import glob
from mock import mock, patch
import settings_mock

from types import MethodType

import os
# Add parent directory for imports, so activity classes can use elife-poa-xml-generation
parentdir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.sys.path.insert(0, parentdir)

class TestPublishFinalPOA(unittest.TestCase):

    def setUp(self):
        self.poa = activity_PublishFinalPOA(settings_mock, None, None, None, None)

        self.do_activity_passes = []

        self.do_activity_passes.append({
            "outbox_file_list": [],
            "done_dir_file_count": 0,
            "approve_status": False,
            "publish_status": None,
            "activity_status": True,
            "output_dir_files": []
        })

        # Missing a PDF
        self.do_activity_passes.append({
            "outbox_file_list": ["elife_poa_e13833.xml", "elife_poa_e13833_ds.zip"],
            "done_dir_file_count": 0,
            "approve_status": True,
            "publish_status": True,
            "activity_status": True,
            "output_dir_files": []
        })

        # Full set of files for one article
        self.do_activity_passes.append({
            "outbox_file_list": ["decap_elife_poa_e13833.pdf", "elife_poa_e13833.xml",
                                 "elife_poa_e13833_ds.zip"],
            "done_dir_file_count": 3,
            "approve_status": True,
            "publish_status": True,
            "activity_status": True,
            "output_dir_files": ["elife-13833-poa-r1.zip"]
        })

        # One article with no ds.zip file
        self.do_activity_passes.append({
            "outbox_file_list": ["decap_elife_poa_e14692.pdf", "elife_poa_e14692.xml"],
            "done_dir_file_count": 2,
            "approve_status": True,
            "publish_status": True,
            "activity_status": True,
            "output_dir_files": ["elife-14692-poa-r1.zip"]
        })

        # Full set of files for two articles
        self.do_activity_passes.append({
            "outbox_file_list": ["decap_elife_poa_e13833.pdf", "elife_poa_e13833.xml",
                                 "elife_poa_e13833_ds.zip",
                                 "decap_elife_poa_e14692.pdf", "elife_poa_e14692.xml",
                                 "elife_poa_e14692_ds.zip"],
            "done_dir_file_count": 6,
            "approve_status": True,
            "publish_status": True,
            "activity_status": True,
            "output_dir_files": ["elife-13833-poa-r1.zip", "elife-14692-poa-r1.zip"]
        })

    def tearDown(self):
        self.poa.clean_tmp_dir()

    def count_files_in_dir(self, dir_name):
        """
        After do_activity, check the directory contains a zip with ds_zip file name
        """
        file_names = glob.glob(dir_name + os.sep + "*")
        return len(file_names)
        
    def compare_files_in_dir(self, dir_name, file_list):
        """
        Compare the file names in the directroy to the file_list provided
        """
        file_names = glob.glob(dir_name + os.sep + "*")
        # First check the count is the same
        if len(file_list) != len(file_names):
            return False
        # Then can compare file name by file name
        for file in file_names:
            file_name = file.split(os.sep)[-1]
            if file_name not in file_list:
                return False
        return True

    def fake_download_files_from_s3(self, file_list):
        for file in file_list:
            source_doc = "tests/test_data/poa/outbox/" + file
            print source_doc
            dest_doc = self.poa.INPUT_DIR + os.sep + file
            print dest_doc
            shutil.copy(source_doc, dest_doc)

    def fake_clean_tmp_dir(self):
        """
        Disable the default clean_tmp_dir() when do_activity runs
        so tests can introspect the files first
        Then can run clean_tmp_dir() in the tearDown later
        """
        pass

    def remove_files_from_tmp_dir_subfolders(self):
        """
        Run between each test pass, delete the subfolders in tmp_dir
        """
        for directory in os.listdir(self.poa.get_tmp_dir()):
            directory_full_path = self.poa.get_tmp_dir() + os.sep + directory
            if os.path.isdir(directory_full_path):
                for file in glob.glob(directory_full_path + "/*"):
                    os.remove(file)

    @patch.object(activity_PublishFinalPOA, 'get_pub_date_str_from_lax')
    @patch.object(activity_PublishFinalPOA, 'upload_xml_to_outbox_s3')
    @patch.object(activity_PublishFinalPOA, 'upload_files_to_s3')
    @patch.object(activity_PublishFinalPOA, 'next_revision_number')
    @patch.object(activity_PublishFinalPOA, 'download_files_from_s3')
    @patch.object(activity_PublishFinalPOA, 'clean_tmp_dir')
    def test_do_activity(self, fake_clean_tmp_dir, fake_download_files_from_s3,
                         fake_next_revision_number, fake_upload_files_to_s3,
                         fake_upload_xml_to_outbox_s3, fake_get_pub_date_str_from_lax):

        fake_clean_tmp_dir = self.fake_clean_tmp_dir()
        fake_next_revision_number.return_value = 1
        fake_upload_files_to_s3.return_value = True
        fake_get_pub_date_str_from_lax.return_value = "20160704000000"

        for test_data in self.do_activity_passes:

            fake_download_files_from_s3 = self.fake_download_files_from_s3(
                test_data["outbox_file_list"])

            param_data = None
            success = self.poa.do_activity(param_data)

            self.assertEqual(self.poa.approve_status, test_data["approve_status"])
            self.assertEqual(self.poa.publish_status, test_data["publish_status"])
            self.assertEqual(self.count_files_in_dir(self.poa.DONE_DIR),
                             test_data["done_dir_file_count"])
            self.assertEqual(self.poa.activity_status, test_data["activity_status"])
            self.assertTrue(self.compare_files_in_dir(self.poa.OUTPUT_DIR,
                                                      test_data["output_dir_files"]))
            self.assertEqual(True, success)
            
            # Clean the tmp_dir subfolders between tests
            self.remove_files_from_tmp_dir_subfolders()


if __name__ == '__main__':
    unittest.main()

import base64
from requests.auth import HTTPBasicAuth
import activity
import json
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from provider.execution_context import Session
import datetime
import boto.sqs
from boto.sqs.message import Message

"""
activity_PostEIF.py activity
"""
import requests


class activity_PostEIF(activity.activity):
    def __init__(self, settings, logger, conn=None, token=None, activity_task=None):
        activity.activity.__init__(self, settings, logger, conn, token, activity_task)

        self.name = "PostEIF"
        self.version = "1"
        self.default_task_heartbeat_timeout = 30
        self.default_task_schedule_to_close_timeout = 60 * 5
        self.default_task_schedule_to_start_timeout = 30
        self.default_task_start_to_close_timeout = 60 * 5
        self.description = "Post a EIF JSON file to a REST service"
        self.logger = logger

    def do_activity(self, data=None):
        """
        Do the work
        """
        if self.logger:
            self.logger.info('data: %s' % json.dumps(data, sort_keys=True, indent=4))

        session = Session(self.settings)
        version = session.get_value(self.get_workflowId(), 'version')
        article_id = session.get_value(self.get_workflowId(), 'article_id')
        run = session.get_value(self.get_workflowId(), 'run')

        self.emit_monitor_event(self.settings, article_id, version, run, "Post EIF", "start",
                                "Starting submission of article EIF " + article_id)

        try:
            eif_filename = session.get_value(self.get_workflowId(), 'eif_filename')
            eif_bucket = self.settings.publishing_buckets_prefix + self.settings.eif_bucket

            if self.logger:
                self.logger.info("Posting file %s" % eif_filename)

            conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
            bucket = conn.get_bucket(eif_bucket)
            key = Key(bucket)
            key.key = eif_filename
            json_output = key.get_contents_as_string()
            destination = self.settings.drupal_EIF_endpoint

            headers = {'content-type': 'application/json'}
            
            auth = None
            if self.settings.drupal_update_user and self.settings.drupal_update_user != '':
                auth = requests.auth.HTTPBasicAuth(self.settings.drupal_update_user,
                                                    self.settings.drupal_update_pass)
                        
            r = requests.post(destination, data=json_output, headers=headers, auth=auth)
            self.logger.info("POST response was %s" % str(r.status_code))
            self.emit_monitor_event(self.settings, article_id, version, run, "Post EIF", "start",
                                    "Finish submission of article " + article_id +
                                    " for version " + str(version) + " run " + str(run) + " the response status "
                                                                                          "was " + str(r.status_code))
            # TODO: this is temp
            if r.status_code == 200:
            #if True:
                # TODO : article path will at some point be available in the respose
                article_path = session.get_value(self.get_workflowId(), 'article_path')
                self.set_monitor_property(self.settings, article_id, 'path', article_path, 'text', version=version)

                published = r.json().get('publish')
                # TODO: this is temp
                #published = False

                # assemble data to start post-publication workflow
                expanded_folder = session.get_value(self.get_workflowId(), 'expanded_folder')
                status = session.get_value(self.get_workflowId(), 'status')

                try:
                    update_date = session.get_value(self.get_workflowId(), 'update_date')
                except:
                    # Default
                    update_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

                follow_on_data = {
                    'article_id': article_id,
                    'version': version,
                    'expanded_folder': expanded_folder,
                    'update_date': update_date,
                    'run': run,
                    'status': status,
                    'eif_location': eif_filename,
                 }

                message = {
                    'workflow_name': 'PostPerfectPublication',
                    'workflow_data': follow_on_data
                }

                if published is True:
                    self.set_monitor_property(self.settings, article_id, 'publication-status', 'published', "text", version=version)

                    # initiate post-publication workflow now

                    sqs_conn = boto.sqs.connect_to_region(self.settings.sqs_region,
                                                          aws_access_key_id=self.settings.aws_access_key_id,
                                                          aws_secret_access_key=self.settings.aws_secret_access_key)

                    out_queue = sqs_conn.get_queue(self.settings.workflow_starter_queue)
                    m = Message()
                    m.set_body(json.dumps(message))
                    out_queue.write(m)
                else:
                    encoded_message = base64.encodestring(json.dumps(message))
                    # store message in dashboard for later
                    self.set_monitor_property(self.settings, article_id, "_publication-data", encoded_message, "text", version=version)
                    self.set_monitor_property(self.settings, article_id, "publication-status", "ready to publish", "text", version=version)
            else:
                self.emit_monitor_event(self.settings, article_id, version, run, "Post EIF", "error",
                                        "Website ingest returned an error code: " + str(r.status_code))
                self.logger.error("Body:" + r.text)
                return False
            self.emit_monitor_event(self.settings, article_id, version, run, "Post EIF", "end",
                                    "Finished submitting EIF for article  " + article_id +
                                    " status was " + str(r.status_code))

        except Exception as e:
            self.logger.exception("Exception when submitting article EIF")
            self.emit_monitor_event(self.settings, article_id, version, run, "Post EIF", "error",
                                    "Error submitting EIF For article" + article_id + " message:" + str(e.message))
            return False
        return True

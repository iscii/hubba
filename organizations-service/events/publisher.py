from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToJson
from events.protobuf_files.events_pb2 import Event
from logger import LoggerFactory
from config import *
import threading
import json

class EventPublisher():
    def __init__(self, domain):
        logger_factory = LoggerFactory()
        self.logger = logger_factory.get_logger()

        self.domain = domain

        project_id = PROJECT_ID
        events_topic = EVENTS_EVENT_TOPIC_ID
        organizations_topic = ORGANIZATIONS_EVENT_TOPIC_ID

        self.logger.info(f"Using project_id: {project_id}")
        self.logger.info(f"Using events_topic: {events_topic}")

        if SERVICE_ACCOUNT is not None and not SERVICE_ACCOUNT:
            credentials = service_account.Credentials.from_service_account_file("./events/hubba-credentials.json")
        else:
            self.logger.info("Using service account from environment variable")
            SA_json = json.loads(SERVICE_ACCOUNT)
            credentials = service_account.Credentials.from_service_account_info(SA_json)

        self.events_publisher_client = pubsub_v1.PublisherClient(credentials=credentials, 
                                                publisher_options = pubsub_v1.types.PublisherOptions(
                                                enable_message_ordering=True))
        self.events_topic_path = self.events_publisher_client.topic_path(project_id, events_topic)

    def publish(self, action, uuid):
        event = Event()
        event.domain = self.domain
        event.action = action
        event.uuid = uuid
        event_json = MessageToJson(event)
        encoded_message = str(event_json).encode("utf-8")
        thread = threading.Thread(target=self._publish, name="publish", args=(encoded_message, uuid))
        thread.start()

    def _publish(self, encoded_message, uuid):
        events_future = self.events_publisher_client.publish(self.events_topic_path, data=encoded_message, ordering_key=uuid)

        self.logger.info(f"Published message {events_future.result()}")

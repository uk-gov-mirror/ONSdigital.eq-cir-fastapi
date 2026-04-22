from firebase_admin import firestore
from google.cloud.firestore import Query, Transaction

from app.config import logging
from app.models.responses import CiMetadata
from app.repositories.buckets.bucket_loader import BucketLoader
from app.repositories.buckets.ci_schema_bucket_repository import (
    CiSchemaBucketRepository,
)
from app.repositories.firebase.firebase_loader import FirebaseLoader
from app.services.ci_schema_location_service import CiSchemaLocationService

logger = logging.getLogger(__name__)


class CiFirebaseRepository:
    """Provides methods to perform actions on firestore using the google firestore client"""

    def __init__(self, bucket_loader: BucketLoader, firebase_loader: FirebaseLoader) -> None:
        """
        Initialises the google firestore client and sets the target collection based on
        `settings.PROJECT_ID`, `settings.FIRESTORE_DB_NAME` and `settings.CI_FIRESTORE_COLLECTION_NAME`
        """
        self.client = firebase_loader.get_client()
        self.ci_collection = firebase_loader.get_ci_collection()
        self.ci_bucket_repository = CiSchemaBucketRepository(bucket_loader)

    def update_ci_metadata(self, guid: str, metadata: CiMetadata):
        """
        Updates metadata of CI.

        Parameters:
        guid (str): identifier of metadata.
        metadata (CiMetadata): metadata for schema
        """
        self.ci_collection.document(guid).update(metadata.model_dump())

    def get_latest_ci_metadata(self, survey_id, classifier_type, classifier_value, language) -> CiMetadata | None:
        """
        Get metadata of latest CI version.

        Parameters:
        survey_id (str): the survey id of the CI metadata.
        form_type (str): the form type of the CI metadata.
        language (str): the language of the CI metadata.
        """
        latest_ci_metadata = (
            self.ci_collection.where("survey_id", "==", survey_id)
            .where("classifier_type", "==", classifier_type)
            .where("classifier_value", "==", classifier_value)
            .where("language", "==", language)
            .order_by("ci_version", direction=Query.DESCENDING)
            .limit(1)
            .stream()
        )

        ci_metadata = None
        for returned_metadata in latest_ci_metadata:
            ci_metadata = CiMetadata(**returned_metadata.to_dict())

        return ci_metadata

    def perform_new_ci_transaction(
        self,
        ci_id: str,
        next_version_ci_metadata: CiMetadata,
        ci: dict,
        stored_ci_filename: str,
    ) -> None:
        """
        A transactional function that wrap CI creation and CI storage processes

        Parameters:
        ci_id (str): The unique id of the new CI.
        next_version_ci_metadata (CiMetadata): The CI metadata being added to firestore.
        ci (dict): The CI being stored.
        stored_ci_filename (str): Filename of uploaded json CI.
        """

        # A stipulation of the @firestore.transactional decorator is the first parameter HAS
        # to be 'transaction', but since we're using classes the first parameter is always
        # 'self'. Encapsulating the transaction within this function circumvents the issue.

        @firestore.transactional
        def post_ci_transaction_run(transaction: Transaction):
            self.create_ci_in_transaction(transaction, ci_id, next_version_ci_metadata)
            self.ci_bucket_repository.store_ci_schema(stored_ci_filename, ci)

        post_ci_transaction_run(self.client.transaction())

    def create_ci_in_transaction(
        self,
        transaction: Transaction,
        ci_id: str,
        ci_metadata: CiMetadata,
    ) -> None:
        """
        Creates a new CI metadata entry in firestore.

        Parameters:
        ci_id (str): The unique id of the new CI.
        ci_metadata (CiMetadata): The CI metadata being added to firestore.
        """
        # Add new version using `model_dump` method to generate dictionary of metadata. This
        # removes `sds_schema` key if not filled

        transaction.set(
            self.ci_collection.document(ci_id),
            ci_metadata.model_dump(),
            merge=True,
        )

    def get_ci_metadata_collection(self, survey_id: str, classifier_type, classifier_value, language: str) -> list[CiMetadata]:
        """
        Gets the collection of CI metadata with a specific survey_id, form_type, language.

        Parameters:
        survey_id (str): The survey id of the CI metadata being collected.
        form_type (str): The form type of the CI metadata being collected.
        language (str): The language of the CI metadata being collected.
        """
        returned_ci_metadata = (
            self.ci_collection.where("survey_id", "==", survey_id)
            .where("classifier_type", "==", classifier_type)
            .where("classifier_value", "==", classifier_value)
            .where("language", "==", language)
            .order_by("ci_version", direction=Query.DESCENDING)
            .stream()
        )

        ci_metadata_list: list[CiMetadata] = []
        for ci_metadata in returned_ci_metadata:
            metadata = CiMetadata(**ci_metadata.to_dict())
            ci_metadata_list.append(metadata)

        return ci_metadata_list

    def get_all_ci_metadata_collection(self) -> list[CiMetadata]:
        """
        Gets the collection of all CI metadata.
        """
        returned_ci_metadata = self.ci_collection.order_by(
            "ci_version",
            direction=Query.DESCENDING,
        ).stream()

        ci_metadata_list: list[CiMetadata] = []
        for ci_metadata in returned_ci_metadata:
            metadata = CiMetadata(**ci_metadata.to_dict())
            ci_metadata_list.append(metadata)

        return ci_metadata_list

    def get_ci_metadata_with_id(self, guid: str) -> CiMetadata | None:
        """
        Gets CI metadata using guid

        Parameters:
        guid (str): The guid of the CI metadata being collected.
        """
        retrieved_ci_metadata = self.ci_collection.where("guid", "==", guid).stream()

        ci_metadata = None
        for returned_metadata in retrieved_ci_metadata:
            ci_metadata = CiMetadata(**returned_metadata.to_dict())

        return ci_metadata

    def get_ci_metadata_collection_with_survey_id(self, survey_id: str) -> list[CiMetadata]:
        """
        Gets the collection of CI metadata using survey_id

        Parameters:
        survey_id (str): The survey id of the CI metadata being collected.
        """
        returned_ci_metadata = (
            self.ci_collection.where("survey_id", "==", survey_id).order_by("ci_version", direction=Query.DESCENDING).stream()
        )

        ci_metadata_list: list[CiMetadata] = []
        for ci_metadata in returned_ci_metadata:
            metadata = CiMetadata(**ci_metadata.to_dict())
            ci_metadata_list.append(metadata)

        return ci_metadata_list

    def perform_delete_ci_transaction(self, ci_metadata_collection: list[CiMetadata]) -> None:
        """
        A transactional function that wrap CI deletion and schema deletion processes

        Parameters:
        ci_metadata_collection (list[CiMetadata]): The CI metadata collection being deleted.
        """
        # A stipulation of the @firestore.transactional decorator is the first parameter HAS
        # to be 'transaction', but since we're using classes the first parameter is always
        # 'self'. Encapsulating the transaction within this function circumvents the issue.

        @firestore.transactional
        def delete_ci_transaction_run(transaction: Transaction, ci_metadata: CiMetadata):
            # Delete ci metadata from FireStore
            self.delete_ci_metadata_collection_in_transaction(transaction, ci_metadata)

            # Delete ci schema from bucket
            stored_ci_filename = CiSchemaLocationService.get_ci_schema_location(ci_metadata)
            self.ci_bucket_repository.delete_ci_schema(stored_ci_filename)

        for ci_metadata in ci_metadata_collection:
            delete_ci_transaction_run(self.client.transaction(), ci_metadata)

    def delete_ci_metadata_collection_in_transaction(self, transaction: Transaction, ci_metadata: CiMetadata):
        """
        For internal use only - deletes document from remote firestore database

        Parameters:
        transaction (Transaction): The transaction object.
        ci_metadata (CiMetadata): The CI metadata being deleted.
        """
        key = ci_metadata.guid

        transaction.delete(self.ci_collection.document(key))

    def update_validator_version_and_ci(self, ci: dict, ci_metadata: CiMetadata):
        """
              Updates ci in bucket

              Parameters:
              guid: identifier for ci
              ci: ci data
              """
        stored_ci_filename = CiSchemaLocationService.get_ci_schema_location(ci_metadata)
        self.update_ci_metadata(ci_metadata.guid, ci_metadata)
        self.ci_bucket_repository.store_ci_schema(stored_ci_filename, ci)

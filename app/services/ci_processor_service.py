from app.config import logging, settings
from app.events.publisher import Publisher
from app.exception import exceptions
from app.models.requests import PostCiSchemaV1Data
from app.models.responses import CiMetadata, CiValidatorMetadata
from app.repositories.buckets.bucket_loader import BucketLoader
from app.repositories.buckets.ci_schema_bucket_repository import CiSchemaBucketRepository
from app.repositories.firebase.ci_firebase_repository import CiFirebaseRepository
from app.services.ci_classifier_service import CiClassifierService
from app.services.ci_schema_location_service import CiSchemaLocationService
from app.services.datetime_service import DatetimeService
from app.services.document_version_service import DocumentVersionService

logger = logging.getLogger(__name__)


class CiProcessorService:
    def __init__(self, bucket_loader: BucketLoader, publisher: Publisher) -> None:
        self.ci_firebase_repository = CiFirebaseRepository(bucket_loader)
        self.ci_bucket_repository = CiSchemaBucketRepository(bucket_loader)
        self.publisher = publisher

    # Posts new CI metadata to Firestore
    def process_raw_ci(self, post_data: PostCiSchemaV1Data, ci_id, validator_version = "", ci_version = "") -> CiMetadata:
        """
        Processes incoming ci

        Parameters:
        post_data (PostCiSchemaV1Data): incoming CI metadata
        """

        ci = post_data.__dict__

        # Get classifier type and value from ci
        classifier_type = CiClassifierService.get_classifier_type(ci)
        classifier_value = CiClassifierService.get_classifier_value(ci, classifier_type)
        # Clean up unused classifier fields in ci
        ci = CiClassifierService.clean_ci_unused_classifier(ci, classifier_type)

        metadata = self.get_ci_metadata_with_id(ci_id)

        if metadata:
            raise exceptions.ExceptionMissingInvalidGuid

        next_version_ci_metadata = self.build_next_version_ci_metadata(
            ci_id,
            validator_version,
            classifier_type,
            classifier_value,
            post_data,
            ci_version
        )

        stored_ci_filename = CiSchemaLocationService.get_ci_schema_location(next_version_ci_metadata)

        self.process_raw_ci_in_transaction(ci_id, next_version_ci_metadata, ci, stored_ci_filename)
        logger.debug(f"New CI created: {next_version_ci_metadata.model_dump()}")

        # create event message
        event_message = CiMetadata(
            ci_version=next_version_ci_metadata.ci_version,
            validator_version=validator_version,
            data_version=next_version_ci_metadata.data_version,
            classifier_type=next_version_ci_metadata.classifier_type,
            classifier_value=next_version_ci_metadata.classifier_value,
            guid=next_version_ci_metadata.guid,
            language=next_version_ci_metadata.language,
            published_at=next_version_ci_metadata.published_at,
            sds_schema=next_version_ci_metadata.sds_schema,
            survey_id=next_version_ci_metadata.survey_id,
            title=next_version_ci_metadata.title,
        )

        self.try_publish_ci_metadata_to_topic(event_message)

        return next_version_ci_metadata

    def process_raw_ci_in_transaction(
            self,
            ci_id: str,
            next_version_ci_metadata: CiMetadata,
            ci: dict,
            stored_ci_filename: str,
    ):
        """
        Process the new CI by calling a transactional function that wrap the procedures
        Commit if the function is sucessful, rolling back otherwise.

        Parameters:
        ci_id (str): The unique id of the new CI.
        next_version_ci_metadata (CiMetadata): The CI metadata being added to firestore.
        ci (dict): The CI being stored.
        stored_ci_filename (str): Filename of uploaded json CI.
        """
        try:
            logger.info("Beginning CI transaction...")
            self.ci_firebase_repository.perform_new_ci_transaction(ci_id,
                                                                   next_version_ci_metadata,
                                                                   ci,
                                                                   stored_ci_filename)

            logger.info("CI transaction committed successfully.")
            return next_version_ci_metadata

        except Exception as exc:
            logger.error(f"Performing CI transaction: exception raised: {exc}")
            logger.error("Rolling back CI transaction")
            raise exceptions.GlobalException from exc

    def build_next_version_ci_metadata(
            self,
            ci_id: str,
            validator_version: str,
            classifier_type: str,
            classifier_value: str,
            post_data: PostCiSchemaV1Data,
            ci_version
    ) -> CiMetadata:
        """
        Builds the next version of CI metadata.

        Parameters:
        ci_id (str): the guid of the metadata.
        validator_version (str): validator version of schema
        classifier_type (str): the classifier type used.
        classifier_value (str): the classier value
        post_data (PostCiSchemaV1Data): the sds schema of the schema.

        Returns:
        CiMetadata: the next version of CI metadata.
        """
        current_ci_version = self.calculate_next_ci_version(post_data.survey_id, classifier_type, classifier_value, post_data.language)

        ci_version = self.validate_ci_version(ci_version, current_ci_version)


        next_version_ci_metadata = CiMetadata(
            guid=ci_id,
            ci_version=int(ci_version),
            validator_version=validator_version,
            data_version=post_data.data_version,
            classifier_type=classifier_type,
            classifier_value=classifier_value,
            language=post_data.language,
            published_at=str(DatetimeService.get_current_date_and_time().strftime(settings.PUBLISHED_AT_FORMAT)),
            sds_schema=post_data.sds_schema,
            survey_id=post_data.survey_id,
            title=post_data.title,
        )
        return next_version_ci_metadata

    def validate_ci_version(self, ci_version: str, current_ci_version: int) -> int:
        try:
            if ci_version == "" or ci_version is None:
                ci_version = current_ci_version
            elif int(ci_version) < current_ci_version:
                raise exceptions.GlobalException()
        except Exception as exc:
            raise exceptions.ExceptionInvalidCiVersion from exc
        return int(ci_version)

    def calculate_next_ci_version(self, survey_id: str, classifier_type, classifier_value, language: str) -> int:
        """
        Calculates the next schema version for the metadata being built.

        Parameters:
        survey_id (str): the survey id of the schema.
        """

        current_version_metadata = self.ci_firebase_repository.get_latest_ci_metadata(
            survey_id, classifier_type, classifier_value, language
        )

        return DocumentVersionService.calculate_ci_version(current_version_metadata)

    def try_publish_ci_metadata_to_topic(self, post_ci_event: CiMetadata) -> None:
        """
        Publish CI metadata to pubsub topic

        Parameters:
        next_version_ci_metadata (CiMetadata): the CI metadata of the newly published CI
        """
        try:
            logger.info("Publishing CI metadata to topic...")
            self.publisher.publish_message(post_ci_event)
            logger.debug(f"CI metadata {post_ci_event} published to topic")
            logger.info("CI metadata published successfully.")
        except Exception as exc:
            logger.debug(f"CI metadata {post_ci_event} failed to publish to topic with error {exc}")
            logger.error("Error publishing CI metadata to topic.")
            raise exceptions.GlobalException from exc

    def get_ci_metadata_collection(self,
                                   survey_id: str,
                                   classifier_type,
                                   classifier_value,
                                   language: str) -> list[CiMetadata]:
        """
        Get a list of CI metadata

        Parameters:
        survey_id (str): the survey id of the schemas.
        classifier_type (str): the classifier type used.
        classifier_value (str): the classier value
        language (str): the language of the schemas.

        Returns:
        List of CiMetadata: the list CI metadata of the requested CI
        """
        logger.info("Retrieving CI metadata...")

        ci_metadata_collection = self.ci_firebase_repository.get_ci_metadata_collection(
            survey_id, classifier_type, classifier_value, language
        )

        return ci_metadata_collection

    def get_all_ci_metadata_collection(self) -> list[CiMetadata]:
        """
        Get a list of all CI metadata

        Returns:
        List of CiMetadata: the list CI metadata of all CI
        """
        logger.info("Retrieving all CI metadata...")

        ci_metadata_collection = self.ci_firebase_repository.get_all_ci_metadata_collection()

        return ci_metadata_collection

    def get_ci_validator_metadata_collection(self) -> list[CiValidatorMetadata]:
        """
        Get a list of all CI validator metadata

        Returns:
        List of CiMetadata: the list CI metadata of all CI validators
        """
        logger.info("Retrieving all CI validator metadata...")

        ci_metadata_list: list[CiMetadata] = self.ci_firebase_repository.get_all_ci_metadata_collection()

        # Cast CiMetadata to CiValidatorMetadata
        ci_validator_metadata_list: list[CiValidatorMetadata] = []
        for ci_metadata in ci_metadata_list:
            metadata = CiValidatorMetadata(**ci_metadata.model_dump())
            ci_validator_metadata_list.append(metadata)

        return ci_validator_metadata_list

    def get_latest_ci_metadata(
            self, survey_id: str, classifier_type: str, classifier_value: str, language: str
    ) -> CiMetadata | None:
        """
        Get the latest CI metadata

        Parameters:
        survey_id (str): the survey id of the schemas.
        form_type (str): the form type of the schemas.
        language (str): the language of the schemas.

        Returns:
        str: the latest CI schema id
        """
        logger.info("Getting latest CI metadata...")

        latest_ci_metadata = self.ci_firebase_repository.get_latest_ci_metadata(
            survey_id, classifier_type, classifier_value, language
        )

        return latest_ci_metadata

    def get_ci_metadata_with_id(self, guid: str) -> CiMetadata | None:
        """
        Get a CI metadata with id

        Parameters:
        query_params (GetCiSchemaV2Params): incoming CI metadata query parameters

        Returns:
        CiMetadata: the CI metadata of the requested CI
        """
        logger.info("Getting CI metadata with id...")

        ci_metadata = self.ci_firebase_repository.get_ci_metadata_with_id(guid)

        return ci_metadata

    def get_ci_metadata_collection_with_survey_id(self, survey_id: str) -> list[CiMetadata]:
        """
        Get CI metadata collection with survey_id

        Parameters:
        survey_id (str): the survey id of the schemas.

        Returns:
        List of CiMetadata: the list CI metadata of the requested CI
        """
        logger.info("Deleting CI metadata and schema by survey_id...")

        ci_metadata_collection = self.ci_firebase_repository.get_ci_metadata_collection_with_survey_id(survey_id)

        return ci_metadata_collection

    def delete_ci_in_transaction(self, ci_metadata_collection: list[CiMetadata]) -> None:
        """
        Delete CI by calling a transactional function that wrap the procedures

        Parameters:
        ci_metadata_collection (list[CiMetadata]): The CI metadata being deleted.
        """
        try:
            logger.info("Beginning delete CI transaction...")
            self.ci_firebase_repository.perform_delete_ci_transaction(ci_metadata_collection)

            logger.info("Delete CI transaction committed successfully.")

        except Exception as exc:
            logger.error("Rolling back CI transaction")
            raise exceptions.GlobalException from exc

    def update_ci_validator_version(self, guid: str, metadata: CiMetadata):
        """
                Updates CI

                Parameters:
                guid (str): identifier for ci
                metadata (CiMetadata): Schema metadata
                """
        self.ci_firebase_repository.update_ci_metadata(guid, metadata)

    def update_validator_version_and_ci(self, post_data: PostCiSchemaV1Data, ci_metadata: CiMetadata):
        ci = post_data.__dict__
        ci_metadata.published_at = str(DatetimeService.get_current_date_and_time().strftime(settings.PUBLISHED_AT_FORMAT))
        self.ci_firebase_repository.update_validator_version_and_ci(ci, ci_metadata)

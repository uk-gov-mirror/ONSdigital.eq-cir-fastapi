from google.cloud import exceptions, storage

from app.config import logging, settings
from app.exception.exceptions import ExceptionBucketNotFound

logger = logging.getLogger(__name__)


class BucketLoader:
    ci_schema_bucket: storage.Bucket | None = None
    __storage_client: storage.Client

    def __init__(self, storage_client: storage.Client) -> None:
        self.__storage_client = storage_client

        self.ci_schema_bucket = self._initialise_bucket(settings.CI_STORAGE_BUCKET_NAME)

    def get_ci_schema_bucket(self) -> storage.Bucket:
        """
        Get the ci schema bucket from Google cloud
        """
        return self.ci_schema_bucket

    def _create_bucket(self, bucket_name: str) -> storage.Bucket | None:
        """
        Create a bucket in Google cloud storage

        Parameters:
        bucket_name (str): The bucket name to create

        Returns:
        storage.Bucket | None: The created bucket object or None if the bucket already exists
        """
        try:
            bucket = self.__storage_client.create_bucket(
                bucket_name,
                project=settings.PROJECT_ID,
            )

            logger.debug(f"Bucket created: {bucket_name}")

            return bucket

        except exceptions.Conflict:
            logger.debug("Bucket already exists. Creation is skipped")

            return None

    def _initialise_bucket(self, bucket_name) -> storage.Bucket:
        """
        Connect to google cloud storage client using PROJECT_ID
        For local environment, if bucket does not exist, then create the bucket
        Else connect to the bucket

        Parameters:
        bucket_name (str): The bucket name

        Returns:
        storage.Bucket: The bucket object
        """
        try:
            bucket = self.__storage_client.get_bucket(
                bucket_name,
            )
        except exceptions.NotFound as exc:
            logger.debug("Error getting bucket")

            if settings.CONF != "local-docker":
                raise ExceptionBucketNotFound from exc

            # For local environment, if bucket does not exist, create it
            bucket = self._create_bucket(bucket_name)

        return bucket

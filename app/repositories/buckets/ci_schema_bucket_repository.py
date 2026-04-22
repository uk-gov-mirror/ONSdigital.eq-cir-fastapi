import json

from app.config import logging
from app.repositories.buckets.bucket_loader import BucketLoader

logger = logging.getLogger(__name__)


class CiSchemaBucketRepository:
    def __init__(self, bucket_loader: BucketLoader):
        self.bucket = bucket_loader.get_ci_schema_bucket()

    def store_ci_schema(self, blob_name: str, schema: dict) -> None:
        """
        Stores ci schema in google bucket as json.

        Parameters:
        blob_name (str): filename of uploaded json schema.
        schema (Schema): ci schema being stored.
        """
        logger.info("attempting to store schema")
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(schema, indent=2),
            content_type="application/json",
        )
        logger.info(f"successfully stored: {blob_name}")

    def retrieve_ci_schema(self, blob_name: str) -> dict | None:
        """
        Get the CI schema from the ci schema bucket using the filename provided.

        Parameters:
        blob_name (str): filename of the retrieved json schema
        """
        logger.info("attempting to get schema")
        logger.debug(f"get_schema blob_name: {blob_name}")

        blob = self.bucket.blob(blob_name)
        if not blob.exists():
            return None
        data = blob.download_as_string()
        logger.debug(f"get_schema data: {data}")
        return json.loads(data)

    def delete_ci_schema(self, blob_name: str) -> None:
        """
        Deletes the CI schema from the ci schema bucket using the filename provided.

        Parameters:
        blob_name (str): filename of the deleted json schema
        """
        logger.info("attempting to delete schema")

        logger.debug(f"delete_ci_schema: {blob_name}")
        blob = self.bucket.blob(blob_name)
        blob.delete()
        logger.info(f"successfully deleted: {blob_name}")

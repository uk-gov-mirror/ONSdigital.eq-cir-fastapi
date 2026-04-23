from google.cloud.firestore import Client, CollectionReference

from app.config import settings


class FirebaseLoader:
    def __init__(self, firestore_client: Client) -> None:
        self.client = firestore_client
        self.ci_collection = self._set_collection(settings.CI_FIRESTORE_COLLECTION_NAME)

    def get_client(self) -> Client:
        """
        Get the firestore client
        """
        return self.client

    def get_ci_collection(self) -> CollectionReference:
        """
        Get the ci collection from firestore
        """
        return self.ci_collection

    def set_transaction(self):
        """
        Set the transaction for firestore client
        """
        self.client.transaction = self.client.transaction()

    def _set_collection(self, collection) -> CollectionReference:
        """
        Set up the collection reference for schemas and datasets
        """
        return self.client.collection(collection)

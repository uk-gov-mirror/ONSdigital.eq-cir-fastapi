from fastapi import Depends
from google.cloud import firestore, storage
from google.cloud.pubsub_v1 import PublisherClient

from app.config import settings
from app.events.publisher import Publisher
from app.repositories.buckets.bucket_loader import BucketLoader
from app.repositories.firebase.firebase_loader import FirebaseLoader
from app.services.ci_processor_service import CiProcessorService


def get_publisher_service() -> Publisher:
    return Publisher(PublisherClient())


def get_bucket_loader() -> BucketLoader:
    return BucketLoader(storage.Client(project=settings.PROJECT_ID))


def get_firebase_loader() -> FirebaseLoader:
    return FirebaseLoader(firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DB_NAME))


def get_ci_processor_service(
        bucket_loader: BucketLoader = Depends(get_bucket_loader),
        firebase_loader: FirebaseLoader = Depends(get_firebase_loader),
        publisher: Publisher = Depends(get_publisher_service)
) -> CiProcessorService:
    return CiProcessorService(
        bucket_loader=bucket_loader,
        firebase_loader=firebase_loader,
        publisher=publisher
)

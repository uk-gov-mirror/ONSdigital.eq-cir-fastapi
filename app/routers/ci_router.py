from dataclasses import asdict

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

import app.exception.exception_response_models as erm
from app.config import Settings, logging
from app.dependencies import get_ci_processor_service
from app.exception import exceptions
from app.exception.exception_response_models import ExceptionResponseModel
from app.models.classifier import Classifiers
from app.models.requests import (
    DeleteCiV1Params,
    GetCiMetadataV1Params,
    GetCiMetadataV2Params,
    GetCiSchemaV1Params,
    GetCiSchemaV2Params,
    PostCiSchemaV1Data,
    PostCiSchemaV2Params,
    PostCiSchemaV3Params,
)
from app.models.responses import CiMetadata, CiValidatorMetadata
from app.repositories.buckets.ci_schema_bucket_repository import (
    CiSchemaBucketRepository,
)
from app.services.ci_processor_service import CiProcessorService
from app.services.ci_schema_location_service import CiSchemaLocationService
from app.services.create_guid_service import CreateGuidService

router = APIRouter(tags=["legacy"])

logger = logging.getLogger(__name__)
settings = Settings()


@router.delete(
    "/v1/dev/teardown",
    responses={
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_to_delete}},
        },
    },
    deprecated=True)
async def http_delete_ci_v1(
        query_params: DeleteCiV1Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    DELETE method that deletes the CI schema from the bucket as well as the CI metadata from Firestore.
    """
    logger.info("Deleting ci metadata and schema via v1 endpoint...")
    logger.debug(f"Input data: query_params={query_params.__dict__}")

    if query_params.survey_id is None:
        raise exceptions.ExceptionIncorrectKeyNames

    ci_metadata_collection = ci_processor_service.get_ci_metadata_collection_with_survey_id(query_params.survey_id)

    if not ci_metadata_collection:
        logger.error(f"delete_ci_v1: exception raised - No collection instrument found: {asdict(query_params)}")
        raise exceptions.ExceptionNoCIToDelete

    ci_processor_service.delete_ci_in_transaction(ci_metadata_collection)

    logger.info("CI metadata and schema successfully deleted")
    response_content = f"CI metadata and schema successfully deleted for {query_params.survey_id}."
    return JSONResponse(status_code=status.HTTP_200_OK, content=response_content)


# Fetching CI Metadata from Firestore
@router.get(
    "/v1/ci_metadata",
    responses={
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_metadata_exception}},
        },
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
    },
    deprecated=True
)
async def http_get_ci_metadata_v1(
        query_params: GetCiMetadataV1Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    GET method that returns any metadata objects from Firestore that match the parameters passed.
    """
    logger.info("Getting ci metadata via v1 endpoint")
    logger.debug(f"Input data: query_params={query_params.__dict__}")

    if not query_params.params_not_none(query_params.__dict__.keys()):
        raise exceptions.ExceptionIncorrectKeyNames
    if not Classifiers.has_member_key(query_params.classifier_type):
        raise exceptions.ExceptionInvalidClassifier

    ci_metadata_collection = ci_processor_service.get_ci_metadata_collection(
        query_params.survey_id, query_params.classifier_type, query_params.classifier_value, query_params.language
    )

    if not ci_metadata_collection:
        error_message = "get_ci_metadata_v1: exception raised - No collection instrument metadata found"
        logger.error(error_message)
        logger.debug(f"{error_message}:{asdict(query_params)}")
        raise exceptions.ExceptionNoCIMetadata

    # Call model_dump to remove optional fields that are None
    return_ci_metadata_collection = []
    for ci_metadata in ci_metadata_collection:
        return_ci_metadata_collection.append(ci_metadata.model_dump())

    logger.info("CI metadata retrieved successfully.")

    return return_ci_metadata_collection


@router.get(
    "/v2/ci_metadata",
    responses={
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_exception}},
        },
    },
    deprecated=True
)
async def http_get_ci_metadata_v2(
        query_params: GetCiMetadataV2Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    GET method that returns any metadata objects from Firestore that match the parameters passed.
    The user has multiple ways of querying the metadata.
    1. Provide survey_id, form_type, language.
    2. Provide no parameters.
    """
    logger.info("Getting ci metadata via v2 endpoint")
    logger.debug(f"get_ci_metadata_v2: Input data: query_params={query_params.__dict__}")

    # If no parameters are provided, return all CI metadata
    if query_params.params_all_none(query_params.__dict__.keys()):
        ci_metadata_collection = ci_processor_service.get_all_ci_metadata_collection()
    else:
        # If parameters are provided, return CI metadata that matches the parameters
        if not query_params.params_not_none(query_params.__dict__.keys()):
            raise exceptions.ExceptionIncorrectKeyNames
        if not Classifiers.has_member_key(query_params.classifier_type):
            raise exceptions.ExceptionInvalidClassifier
        else:
            ci_metadata_collection = ci_processor_service.get_ci_metadata_collection(
                query_params.survey_id, query_params.classifier_type, query_params.classifier_value,
                query_params.language
            )

    if not ci_metadata_collection:
        error_message = "get_ci_metadata_v2: exception raised - No collection instruments found"
        logger.error(error_message)
        logger.debug(f"{error_message}:{asdict(query_params)}")
        raise exceptions.ExceptionNoCIFound

    # Call model_dump to remove optional fields that are None
    return_ci_metadata_collection = []
    for ci_metadata in ci_metadata_collection:
        return_ci_metadata_collection.append(ci_metadata.model_dump())

    logger.info("CI metadata retrieved successfully.")

    return return_ci_metadata_collection


# Fetching CI schema from Bucket version 1
@router.get(
    "/v1/retrieve_collection_instrument",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully retrieved the CI schema. This is illustrated by returning the CI schema to the user."
            ),
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_exception}},
        },
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
    },
    deprecated=True
)
async def http_get_ci_schema_v1(
        query_params: GetCiSchemaV1Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    GET method that fetches a CI schema by survey_id, form_type and language.
    """
    logger.info("Getting ci schema via v1 endpoint")
    logger.debug(f"get_ci_schema_vi: Getting CI schemaInput data: query_params={query_params.__dict__}")

    if not query_params.params_not_none("survey_id", "classifier_type", "classifier_value", "language"):
        raise exceptions.ExceptionIncorrectKeyNames
    if not Classifiers.has_member_key(query_params.classifier_type):
        raise exceptions.ExceptionInvalidClassifier

    latest_ci_metadata = ci_processor_service.get_latest_ci_metadata(
        query_params.survey_id, query_params.classifier_type, query_params.classifier_value, query_params.language
    )

    if not latest_ci_metadata:
        error_message = "get_ci_schema_v1: exception raised - No CI found for"
        logger.debug(f"{error_message}:{asdict(query_params)}")
        logger.info(error_message)
        raise exceptions.ExceptionNoCIFound

    bucket_schema_filename = CiSchemaLocationService.get_ci_schema_location(latest_ci_metadata)

    logger.info("Bucket schema location successfully retrieved. Getting schema")
    logger.debug(f"Bucket schema location: {bucket_schema_filename}")

    ci_schema = ci_processor_service.ci_bucket_repository.retrieve_ci_schema(bucket_schema_filename)

    if not ci_schema:
        error_message = "get_ci_schema_v1: exception raised - No CI found"
        logger.info(error_message)
        logger.debug(f"{error_message}:{asdict(query_params)}")
        raise exceptions.ExceptionNoCIFound

    logger.info("Schema successfully retrieved.")

    return ci_schema


# Fetching CI schema from Bucket Version 2
@router.get(
    "/v2/retrieve_collection_instrument",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully Queried a CI. This is illustrated with the returned response containing the schema of the CI."
            ),
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_exception}},
        },
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
    },
    deprecated=True
)
async def http_get_ci_schema_v2(
        query_params: GetCiSchemaV2Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    GET method that fetches a CI schema by GUID.
    """
    logger.info("Getting ci schema via v2 endpoint...")
    logger.debug(f"Input data: query_params={query_params.__dict__}")

    if query_params.guid is None:
        raise exceptions.ExceptionIncorrectKeyNames

    ci_metadata = ci_processor_service.get_ci_metadata_with_id(query_params.guid)

    if not ci_metadata:
        error_message = "get_ci_schema_v2: exception raised - No collection instrument metadata found"
        logger.error(error_message)
        logger.debug(f"{error_message}:{query_params.guid}")
        raise exceptions.ExceptionNoCIMetadata

    bucket_schema_filename = CiSchemaLocationService.get_ci_schema_location(ci_metadata)

    logger.info("Bucket schema location successfully retrieved. Getting schema")
    logger.debug(f"Bucket schema location: {bucket_schema_filename}")

    ci_schema = ci_processor_service.ci_bucket_repository.retrieve_ci_schema(bucket_schema_filename)

    if not ci_schema:
        message = "get_ci_schema_v2: exception raised - No CI found for"
        logger.info(message)
        logger.debug(f"{message}:{query_params.guid}")
        raise exceptions.ExceptionNoCIFound

    logger.info("Schema successfully retrieved.")

    return JSONResponse(status_code=status.HTTP_200_OK, content=ci_schema)


@router.post(
    "/v1/publish_collection_instrument",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully created a CI. This is illustrated with the returned response containing the metadata of the CI."
            ),
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
    },
    deprecated=True
)
async def http_post_ci_schema_v1(
        post_data: PostCiSchemaV1Data,
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    POST method that creates a Collection Instrument. This will post the metadata to Firestore and
    the whole request body to a Google Cloud Bucket.
    """
    logger.info("Posting ci schema via v1 endpoint")

    ci_id = CreateGuidService.create_guid()

    ci_metadata = ci_processor_service.process_raw_ci(post_data, ci_id)

    logger.info("CI schema posted successfully")
    return ci_metadata.model_dump()


@router.post(
    "/v2/publish_collection_instrument",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully created a CI. This is illustrated with the returned response containing the "
                    "metadata of the CI. "
            ),
        },
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
    },
    deprecated=True
)
async def http_post_ci_schema_v2(
        post_data: PostCiSchemaV1Data,
        query_params: PostCiSchemaV2Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    POST method that creates a Collection Instrument. This will post the metadata to Firestore and
    the whole request body to a Google Cloud Bucket. Validator version required param.
    """
    logger.info("Posting CI schema via v2 endpoint")

    if query_params.validator_version == "" or query_params.validator_version is None:
        message = "No validation version supplied"
        logger.debug(f"{message}")
        raise exceptions.ExceptionNoValidator

    ci_id = CreateGuidService.create_guid()

    ci_metadata = ci_processor_service.process_raw_ci(post_data, ci_id, query_params.validator_version)

    logger.info("CI schema posted successfully")

    return ci_metadata.model_dump()

@router.post(
    "/v3/publish_collection_instrument",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully created a CI. This is illustrated with the returned response containing the "
                    "metadata of the CI. "
            ),
        },
        400: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_400_incorrect_key_names_exception}},
        },
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
    },
)
async def http_post_ci_schema_v3(
        post_data: PostCiSchemaV1Data,
        query_params: PostCiSchemaV3Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):
    """
    POST method that creates a Collection Instrument. This will post the metadata to Firestore and
    the whole request body to a Google Cloud Bucket.
    guid and validator_version required param with optional ci_version.
    """
    logger.info("Posting CI schema via v3 endpoint")

    if query_params.guid == "" or query_params.guid is None:
        message = "No guid supplied"
        logger.debug(f"{message}")
        raise exceptions.ExceptionMissingInvalidGuid

    if query_params.validator_version == "" or query_params.validator_version is None:
        message = "No validation version supplied"
        logger.debug(f"{message}")
        raise exceptions.ExceptionNoValidator

    ci_metadata = ci_processor_service.process_raw_ci(post_data,
                                                      query_params.guid,
                                                      query_params.validator_version,
                                                      query_params.ci_version)

    logger.info("CI schema posted successfully")

    return ci_metadata.model_dump()


@router.get(
    "/v1/ci_validator_metadata",
    responses={
        500: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_500_global_exception}},
        },
        404: {
            "model": ExceptionResponseModel,
            "content": {"application/json": {"example": erm.erm_404_no_ci_validator_metadata_exception}},
        },
    },
    deprecated=True
)
async def http_get_ci_validator_metadata_v1(
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
) -> list[CiValidatorMetadata]:
    """
    GET method that returns the validator metadata for a CI schema.
    """
    logger.info("Getting ci validator metadata via v1 endpoint")

    ci_validator_metadata_collection = ci_processor_service.get_ci_validator_metadata_collection()

    if not ci_validator_metadata_collection:
        logger.error("No collection instrument validator metadata found")
        raise exceptions.ExceptionNoCIValidatorMetadata

    return ci_validator_metadata_collection

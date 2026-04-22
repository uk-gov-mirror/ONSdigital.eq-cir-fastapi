
from fastapi import APIRouter, Depends

import app.exception.exception_response_models as erm
from app.config import Settings, logging
from app.dependencies import get_ci_processor_service
from app.exception import exceptions
from app.exception.exception_response_models import ExceptionResponseModel
from app.models.requests import (
    PostCiSchemaV1Data,
    UpdateValidatorVersionV1Params,
)
from app.models.responses import CiMetadata
from app.services.ci_processor_service import CiProcessorService

router = APIRouter()

logger = logging.getLogger(__name__)
settings = Settings()

@router.put(
    "/v1/update_validator_version",
    responses={
        200: {
            "model": CiMetadata,
            "description": (
                    "Successfully updated validator version"
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
async def http_put_ci_validator_version_v1(
        post_data: PostCiSchemaV1Data,
        query_params: UpdateValidatorVersionV1Params = Depends(),
        ci_processor_service: CiProcessorService = Depends(get_ci_processor_service),
):

    if not query_params.params_not_none(query_params.__dict__.keys()):
        raise exceptions.ExceptionIncorrectKeyNames

    ci_metadata = ci_processor_service.get_ci_metadata_with_id(query_params.guid)

    if not ci_metadata:
        error_message = "patch_ci_validator: exception raised - No collection instrument metadata found"
        logger.error(error_message)
        logger.debug(f"{error_message}:{query_params.guid}")
        raise exceptions.ExceptionNoCIMetadata

    if ci_metadata.validator_version == query_params.validator_version:
        logger.info("No change to validator_version")
        return ci_metadata.model_dump()

    ci_updated_metadata = ci_metadata.copy()
    ci_updated_metadata.validator_version = query_params.validator_version

    ci_processor_service.update_validator_version_and_ci(post_data, ci_updated_metadata)

    return ci_updated_metadata.model_dump()

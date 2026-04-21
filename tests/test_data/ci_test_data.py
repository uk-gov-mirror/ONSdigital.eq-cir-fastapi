import uuid

from app.config import Settings
from app.models.classifier import Classifiers
from app.models.requests import PostCiSchemaV1Data
from app.models.responses import CiMetadata, CiValidatorMetadata

settings = Settings()


# Mock data for all tests
mock_data_version = "test_data_version"
mock_validator_version_v1 = ""
mock_validator_version_v2 = "0.0.1"
mock_updated_validator_version_v2 = "0.0.2"
mock_classifier_type = Classifiers.FORM_TYPE
mock_classifier_value = "test_form_type"
mock_id = str(uuid.uuid4())
mock_next_version_id = str(uuid.uuid4())
mock_language = "test_language"
mock_sds_schema = ""
mock_survey_id = "test_survey_id"
mock_title = "test_title"
mock_published_at = "2023-04-20T12:00:00.000000Z"

mock_post_ci_schema = PostCiSchemaV1Data(
    survey_id=mock_survey_id,
    language=mock_language,
    form_type=mock_classifier_value,
    title=mock_title,
    data_version=mock_data_version,
    sds_schema=mock_sds_schema,
)

mock_post_ci_schema_without_sds_schema = PostCiSchemaV1Data(
    survey_id=mock_survey_id,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    language=mock_language,
    title=mock_title,
    data_version=mock_data_version,
)

mock_post_ci_schema_with_sds_schema = PostCiSchemaV1Data(
    survey_id=mock_survey_id,
    language=mock_language,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    title=mock_title,
    data_version=mock_data_version,
    sds_schema="0004",
)

mock_ci_metadata = CiMetadata(
    ci_version=1,
    validator_version="",
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_ci_metadata_v2 = CiMetadata(
    ci_version=1,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_ci_metadata_v3 = CiMetadata(
    ci_version=2,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_ci_metadata_v3_auto_version = CiMetadata(
    ci_version=1,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_updated_ci_metadata_v2 = CiMetadata(
    ci_version=1,
    validator_version=mock_updated_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_next_version_ci_metadata = CiMetadata(
    ci_version=2,
    validator_version=mock_validator_version_v1,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_next_version_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_next_version_ci_metadata_v2 = CiMetadata(
    ci_version=2,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_next_version_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_next_version_ci_metadata_v3 = CiMetadata(
    ci_version=100,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_next_version_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_next_version_ci_metadata_v3_auto_version = CiMetadata(
    ci_version=3,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_next_version_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_ci_metadata_v3_with_ci_version = CiMetadata(
    ci_version=1,
    validator_version=mock_validator_version_v2,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

mock_ci_metadata_list = [
    CiMetadata(
        ci_version=1,
        validator_version=mock_validator_version_v1,
        data_version=mock_data_version,
        classifier_type=mock_classifier_type,
        classifier_value=mock_classifier_value,
        guid=mock_id,
        language=mock_language,
        published_at=mock_published_at,
        sds_schema=mock_sds_schema,
        survey_id=mock_survey_id,
        title="test_1",
    ),
    CiMetadata(
        ci_version=2,
        validator_version=mock_validator_version_v1,
        data_version=mock_data_version,
        classifier_type=mock_classifier_type,
        classifier_value=mock_classifier_value,
        guid=mock_id,
        language=mock_language,
        published_at=mock_published_at,
        sds_schema=mock_sds_schema,
        survey_id=mock_survey_id,
        title="test_2",
    ),
]

mock_ci_validator_metadata_list =[
    CiValidatorMetadata(
        survey_id=mock_survey_id,
        classifier_type=mock_classifier_type,
        classifier_value=mock_classifier_value,
        guid=mock_id,
        ci_version=1,
        validator_version=mock_validator_version_v1,
    ),
    CiValidatorMetadata(
        survey_id=mock_survey_id,
        classifier_type=mock_classifier_type,
        classifier_value=mock_classifier_value,
        guid=mock_id,
        ci_version=2,
        validator_version=mock_validator_version_v1,
    ),
]

mock_ci_published_metadata = CiMetadata(
    ci_version=1,
    validator_version=mock_validator_version_v1,
    data_version=mock_data_version,
    classifier_type=mock_classifier_type,
    classifier_value=mock_classifier_value,
    guid=mock_id,
    language=mock_language,
    published_at=mock_published_at,
    sds_schema=mock_sds_schema,
    survey_id=mock_survey_id,
    title=mock_title,
)

# Representative `PubsubMessage` data returned by `Publisher.pull()`
message_data = {
    "ci_version": 2,
    "validator_version": "0.0.1",
    "data_version": "1",
    "classifier_type": "form_type",
    "classifier_value": "business",
    "id": "ca9c5b88-0700-4e87-a90e-0d3e05ae37d5",
    "language": "welsh",
    "published_at": "2023-06-14T08:54:27.722250Z",
    "status": "DRAFT",
    "survey_id": "3456",
    "title": "NotDune",
}

post_data = {
    "data_version": "1",
    "form_type": mock_classifier_value,
    "language": mock_language,
    "survey_id": mock_survey_id,
    "title": "test",
}

"""Configuration options for drf-spectacular."""

from InvenTree.version import inventreeApiVersion


def get_spectacular_settings():
    """Return configuration dictionary for drf-spectacular."""
    return {
        'TITLE': 'InvenTree API',
        'DESCRIPTION': 'API for InvenTree - the intuitive open source inventory management system',
        'LICENSE': {
            'name': 'MIT',
            'url': 'https://github.com/inventree/InvenTree/blob/master/LICENSE',
        },
        'EXTERNAL_DOCS': {
            'description': 'More information about InvenTree in the official docs',
            'url': 'https://docs.inventree.org',
        },
        'VERSION': str(inventreeApiVersion()),
        'SERVE_INCLUDE_SCHEMA': False,
        'SCHEMA_PATH_PREFIX': '/api/',
        'POSTPROCESSING_HOOKS': [
            'InvenTree.schema.postprocess_schema_enums',
            'InvenTree.schema.postprocess_required_nullable',
            'InvenTree.schema.postprocess_print_stats',
        ],
        'ENUM_NAME_OVERRIDES': {
            'UserTypeEnum': 'users.models.UserProfile.UserType',
            'TemplateModelTypeEnum': 'report.models.ReportTemplateBase.ModelChoices',
            'AttachmentModelTypeEnum': 'common.models.Attachment.ModelChoices',
            'ParameterModelTypeEnum': 'common.models.Parameter.ModelChoices',
            'DataImportSessionModelTypeEnum': 'importer.models.DataImportSession.ModelChoices',
            # Allauth
            'UnauthorizedStatus': [[401, 401]],
            'IsTrueEnum': [[True, True]],
        },
        # oAuth2
        'OAUTH2_FLOWS': ['authorizationCode', 'clientCredentials'],
        'OAUTH2_AUTHORIZATION_URL': '/o/authorize/',
        'OAUTH2_TOKEN_URL': '/o/token/',
        'OAUTH2_REFRESH_URL': '/o/revoke_token/',
    }

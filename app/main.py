import boto3
import os
import json
import requests
import glueops.setup_logging
import glueops.getoutline
from aws import AWSOrganization

GETOUTLINE_API_URL = "https://app.getoutline.com"
REQUIRED_ENV_VARS = [
    "GETOUTLINE_DOCUMENT_ID",
    "GETOUTLINE_API_TOKEN",
    "AWS_CREDENTIALS_JSON"
]

OPTIONAL_ENV_VARS = {
    "VERSION": "unknown",
    "COMMIT_SHA": "unknown",
    "BUILD_TIMESTAMP": "unknown",
}

def get_credentials():
    """
    Retrieve AWS credentials from the environment variable.

    :return: List of AWS account credentials.
    :raises EnvironmentError: If the AWS_CREDENTIALS_JSON environment variable is not set.
    :raises ValueError: If the JSON in AWS_CREDENTIALS_JSON is invalid.
    """
    credentials_json = os.getenv('AWS_CREDENTIALS_JSON')
    if not credentials_json:
        raise EnvironmentError("AWS_CREDENTIALS_JSON environment variable not set.")
    
    try:
        credentials = json.loads(credentials_json)
        return credentials['accounts']
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON in AWS_CREDENTIALS_JSON.") 


def get_env_variable(var_name: str, default=None):
    """
    Retrieve environment variable or return default if not set.

    :param var_name: Name of the environment variable.
    :param default: Default value if the environment variable is not set.
    :return: Value of the environment variable or default.
    :raises EnvironmentError: If a required environment variable is not set.
    """
    value = os.getenv(var_name, default)
    if var_name in REQUIRED_ENV_VARS and value is None:
        logger.error(f"Environment variable '{var_name}' is not set.")
        raise EnvironmentError(f"Environment variable '{var_name}' is required but not set.")
    logger.debug(f"Environment variable '{var_name}' retrieved.")
    return value

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = glueops.setup_logging.configure(level=LOG_LEVEL)
logger.info(f"Logger initialized with level: {LOG_LEVEL}")
logger.info({
    "version": os.getenv("VERSION", "unknown"),
    "commit_sha": os.getenv("COMMIT_SHA", "unknown"),
    "build_timestamp": os.getenv("BUILD_TIMESTAMP", "unknown")
})

try:
    GETOUTLINE_DOCUMENT_ID = get_env_variable('GETOUTLINE_DOCUMENT_ID')
    GETOUTLINE_API_TOKEN = get_env_variable('GETOUTLINE_API_TOKEN')
    AWS_CREDENTIALS_JSON = get_env_variable('AWS_CREDENTIALS_JSON')
    get_credentials()
    VERSION = get_env_variable('VERSION', OPTIONAL_ENV_VARS['VERSION'])
    COMMIT_SHA = get_env_variable('COMMIT_SHA', OPTIONAL_ENV_VARS['COMMIT_SHA'])
    BUILD_TIMESTAMP = get_env_variable('BUILD_TIMESTAMP', OPTIONAL_ENV_VARS['BUILD_TIMESTAMP'])
    logger.info("All required environment variables retrieved successfully.")
except EnvironmentError as env_err:
    logger.critical(f"Environment setup failed: {env_err}")
    raise

def main():
    """
    Main function to execute the script.
    """
    try:
        logger.info("Starting script execution.")
        # Initialize GetOutlineClient
        GetOutlineClient = glueops.getoutline.GetOutlineClient(GETOUTLINE_API_URL, GETOUTLINE_DOCUMENT_ID, GETOUTLINE_API_TOKEN)
        parent_id = GetOutlineClient.get_document_uuid()
        children = GetOutlineClient.get_children_documents_to_delete(parent_id)
        
        # Delete existing child documents
        for id in children:
            GetOutlineClient.delete_document(id)

        # Retrieve AWS account credentials
        accounts_creds = get_credentials()
        all_accounts = []
        markdown_content = ""
        
        # Process each AWS account
        for creds in accounts_creds:
            aws_account_name = creds['name']
            access_key = creds['access_key']
            secret_key = creds['secret_key']
            
            aws_org = AWSOrganization(aws_account_name, access_key, secret_key)
            org_client = aws_org.get_aws_client('organizations')
            accounts = aws_org.get_aws_accounts(org_client)
            all_accounts.extend(accounts)
            markdown_content = aws_org.create_markdown(accounts, org_client)
            logger.debug(f"Markdown content: {markdown_content}")
            logger.info(f"Generated Markdown for AWS ORG: {aws_account_name}")
        
            # Create new document in Outline
            GetOutlineClient.create_document(parent_id, aws_account_name, markdown_content)
            logger.info(f"Created {aws_account_name} doc successfully under parent doc: {GETOUTLINE_DOCUMENT_ID}")
            
        logger.info("Script execution completed successfully.")
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise

if __name__ == '__main__':
    main()
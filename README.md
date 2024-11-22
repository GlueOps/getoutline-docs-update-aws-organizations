# getoutline-docs-update-aws-organizations

This project uses `boto3` to interact with AWS Organizations and IAM services to generate a markdown file containing information about AWS accounts and IAM users. The generated markdown includes details such as AWS Account ID, Account Name, Account Email, Created Date, SIGNIN URL, and Description for each account, as well as IAM User Name, Access Key ID, and Description for each IAM user. Once finished the Markdown will be added to our wiki hosted at getoutline.com

## Prerequisites

- Python 3.11
- AWS credentials require these AWS permissions:
  - `arn:aws:iam::aws:policy/AWSOrganizationsReadOnlyAccess`
  - `arn:aws:iam::aws:policy/IAMReadOnlyAccess`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/getoutline-docs-update-aws-organizations.git
    cd getoutline-docs-update-aws-organizations
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Set the required environment variables:
    ```sh
    export GETOUTLINE_DOCUMENT_ID='your_outline_document_id'
    export GETOUTLINE_API_TOKEN='your_outline_api_token'
    export AWS_CREDENTIALS_JSON='your_aws_credentials_json'
    ```

    Example of `AWS_CREDENTIALS_JSON`:
    ```json
    {
        "accounts": [
            {
                "name": "org1",
                "access_key": "your_access_key_id_for_org1",
                "secret_key": "your_secret_access_key_for_org1"
            },
            {
                "name": "org2",
                "access_key": "your_access_key_id_for_org2",
                "secret_key": "your_secret_access_key_for_org2"
            }
        ]
    }
    ```

2. Run the script:
    ```sh
    python app/main.py
    ```

3. The script will generate markdown and nest it under an existing AWS document within our getoutline docs.

## Script Details

### `main.py`

- **get_aws_accounts(org_client)**: Retrieves a list of AWS accounts in the organization.
- **get_account_tags(org_client, account_id)**: Retrieves the tags for a given AWS account.
- **generate_signin_url(account_id)**: Generates the SIGNIN URL for a given AWS account ID.
- **list_iam_users(iam_client)**: Lists all IAM users in the root organization.
- **get_user_access_keys(iam_client, user_name)**: Retrieves the access keys for a given IAM user.
- **create_markdown(accounts, org_client)**: Generates the markdown content for AWS accounts and IAM users.

## Example Output

The generated markdow output will look like this:

```md
| AWS Account ID | Account Name | Account Email | Created Date | SIGNIN URL | Description |
|----------------|--------------|---------------|--------------|------------|-------------|
| 123456789012   | ExampleName  | example@domain.com | 2022-01-01 | https://123456789012.signin.aws.amazon.com/console | Example Description |

| IAM User Name | Access Key ID | Description |
|---------------|---------------|-------------|
| example-user  | AKIAIOSFODNN7EXAMPLE | Example Description |
```
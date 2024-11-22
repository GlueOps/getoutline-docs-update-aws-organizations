import boto3
import os
import json
import glueops.setup_logging

class AWSOrganization:
    def __init__(self, aws_account_name, aws_access_key_id, aws_secret_access_key, log_level="INFO"):
        self.aws_account_name = aws_account_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.logger = glueops.setup_logging.configure(level=log_level)
        self.logger.info(f"Logger initialized with level: {log_level}")

    def get_aws_client(self, service_name):
        """
        Creates a boto3 client for the specified AWS service.

        Args:
            service_name (str): The name of the AWS service.

        Returns:
            boto3.client: The AWS service client.
        """
        return boto3.client(
            service_name, 
            aws_access_key_id=self.aws_access_key_id, 
            aws_secret_access_key=self.aws_secret_access_key
        )

    def get_aws_accounts(self, org_client):
        """
        Retrieves a list of AWS accounts in the organization.

        Args:
            org_client (boto3.client): The AWS Organizations client.

        Returns:
            list: A list of AWS accounts.
        """
        try:
            paginator = org_client.get_paginator('list_accounts')
            accounts = []
            for page in paginator.paginate():
                accounts.extend(page['Accounts'])
            self.logger.info(f"Retrieved {len(accounts)} accounts.")
            return accounts
        except Exception as e:
            self.logger.error(f"Failed to retrieve AWS accounts: {e}")
            raise

    def get_account_tags(self, org_client, account_id):
        """
        Retrieves the tags for a given AWS account.

        Args:
            org_client (boto3.client): The AWS Organizations client.
            account_id (str): The AWS account ID.

        Returns:
            str: The description tag value or 'No Description'.
        """
        try:
            response = org_client.list_tags_for_resource(ResourceId=account_id)
            tags = response['Tags']
            for tag in tags:
                if tag['Key'] == 'Description':
                    return tag['Value']
            return 'No Description'
        except Exception as e:
            self.logger.error(f"Failed to retrieve tags for account {account_id}: {e}")
            raise

    def list_iam_users(self):
        """
        Lists all IAM users in the root organization.

        Returns:
            list: A list of IAM users.
        """
        try:
            iam_client = self.get_aws_client('iam')
            paginator = iam_client.get_paginator('list_users')
            users = []
            for page in paginator.paginate():
                users.extend(page['Users'])
            self.logger.info(f"Retrieved {len(users)} IAM users.")
            return users
        except Exception as e:
            self.logger.error(f"Failed to retrieve IAM users: {e}")
            raise

    def get_user_access_keys(self, user_name):
        """
        Retrieves the access keys for a given IAM user.

        Args:
            user_name (str): The IAM user name.

        Returns:
            list: A list of access key metadata.
        """
        try:
            iam_client = self.get_aws_client('iam')
            response = iam_client.list_access_keys(UserName=user_name)
            return response['AccessKeyMetadata']
        except Exception as e:
            self.logger.error(f"Failed to retrieve access keys for user {user_name}: {e}")
            raise

    def create_markdown(self, accounts, org_client):
        """
        Creates a markdown table with details about the AWS accounts and IAM users.

        Args:
            accounts (list): A list of AWS accounts.
            org_client (boto3.client): The AWS Organizations client.

        Returns:
            str: The markdown content.
        """
        try:
            # Sort accounts by created date (JoinedTimestamp)
            accounts = sorted(accounts, key=lambda x: x['JoinedTimestamp'])
            markdown_content = "> This page is automatically generated. Any manual changes will be lost. See: https://github.com/GlueOps/getoutline-docs-update-aws-organizations \n\n"
            markdown_content += f"# AWS ROOT Organization Details for {self.aws_account_name}\n\n"
            markdown_content += '| AWS Account ID | Account Name | Description | Account Email | Created Date |\n'
            markdown_content += '|----------------|--------------|-------------|---------------|--------------|\n'
            
            for account in accounts:
                account_id = account['Id']
                account_name = account['Name']
                account_email = account['Email']
                created_date = account['JoinedTimestamp'].strftime('%Y-%m-%d')
                description = self.get_account_tags(org_client, account_id)
                markdown_content += f'| {account_id} | {account_name} | {description} | {account_email} | {created_date} |\n'

            markdown_content += '\n\n| IAM User Name | Access Key ID | Description |\n'
            markdown_content += '|---------------|---------------|-------------|\n'
            users = self.list_iam_users()
            for user in users:
                user_name = user['UserName']
                access_keys = self.get_user_access_keys(user_name)
                if not access_keys:
                    markdown_content += f'| {user_name} | No Access Key | No Description |\n'
                else:
                    for access_key in access_keys:
                        access_key_id = access_key['AccessKeyId']
                        description = 'No Description'
                        tags = self.get_aws_client('iam').list_user_tags(UserName=user_name)['Tags']
                        for tag in tags:
                            if tag['Key'] == 'description':
                                description = tag['Value']
                        markdown_content += f'| {user_name} | {access_key_id} | {description} |\n'

            self.logger.info("Markdown content created successfully.")
            return markdown_content
        except Exception as e:
            self.logger.error(f"Failed to create markdown content: {e}")
            raise


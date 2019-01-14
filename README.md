# aws-reporting-scripts
Collected scripts for simple reporting on AWS resources &amp; configuration; Most scripts output simplified and selected information as CSV.

## Usage
Most scripts are simple python scripts that output to stdout. Execute them with:

```
./script_name.py
```

Common arguments:

| Short Option | Long Option | Default  | Notes |
| ------------ | ----------- | -------- | ----- |
| -r           | --region    | [See note below](#Region) | Short region alias (e.g. 'us-east-1'); Or use 'all' for all regions |

### Authentication
By design, these scripts do not handle authentication. Use one of the following methods for authentication with the AWS APIs:
1. [AWS Environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables)
1. [AWS Credentials file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file)
1. [AWS Config file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#aws-config-file)
1. Wrap around or customise the scripts

### Region
If region is not specified, the script will attempt to proceed with the user's default region configured for the AWS SDK:
1. [AWS Environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variable-configuration)
1. [AWS Credentials file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file)
1. [AWS Config file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#aws-config-file)

## Requirements
* Python 3
* Python modules: See [requirements.txt](./requirements.txt)

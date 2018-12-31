# aws-reporting-scripts
Collected scripts for simple reporting on AWS resources &amp; configuration; Most scripts output selected information as a simplified CSV.

## Usage
Most scripts are simple python scripts - execute them with:

```
chmod +x script_name.py
./script_name.py
```

Or:

```
python3 script_name.py
```

### Authentication
By design, these scripts do not handle authentication. Use one of the following methods for authentication with the AWS APIs:
1. [Environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables)
1. [AWS Credentials file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file)
1. [AWS Config file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#aws-config-file)
1. Wrap around or customise the scripts

## Requirements
* Python 3
* Python modules: See [requirements.txt](./requirements.txt)

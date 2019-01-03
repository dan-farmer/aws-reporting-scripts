#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""Common functions for aws-reporting-scripts"""

import sys
import boto3
import botocore.exceptions

def get_regions():
    """Return list of AWS regions."""
    try:
        ec2_client = boto3.client('ec2')
    except botocore.exceptions.NoRegionError:
        # If we fail because the user has no default region, use us-east-1
        # This is for listing regions only
        # Iterating resources is then performed in each region
        ec2_client = boto3.client('ec2', region_name='us-east-1')
    try:
        region_list = ec2_client.describe_regions()['Regions']
    except botocore.exceptions.ClientError as err:
        # Handle auth errors etc
        # It is possible for our auth details to expire between this and any later request;
        # We consider this an acceptable race condition
        print('ERROR: {0}'.format(err), file=sys.stderr)
        sys.exit(10)
    for region in region_list:
        yield region['RegionName']

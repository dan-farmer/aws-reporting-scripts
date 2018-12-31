#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List EC2 instances, SSM agent and platform details as CSV."""

import sys
import csv
try:
    import boto3
    import botocore.exceptions
except ImportError as err:
    print('ERROR: {0}'.format(err), file=sys.stderr)
    raise err

def main():
    """Gather and write CSV data, one row per Instance.

    Iterate through available AWS regions
    Iterate through all EC2 instances
    Query basic EC2 instance information (Name tag, EC2 platform)
    Query SSM agent version, status, platform information
    """

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_ALL)

    # Header row
    output.writerow(['Region',
                     'InstanceID',
                     'Name',
                     'EC2Platform',
                     'SSMPingStatus',
                     'SSMAgentVersion',
                     'SSMPlatformType',
                     'SSMPlatformName',
                     'SSMPlatformVersion'])

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
        # Note that it is possible for our auth details to expire between this
        # and any later request; We consider this an acceptable race condition
        print('ERROR: {0}'.format(err), file=sys.stderr)
        raise err
    for region in region_list:
        yield region['RegionName']

if __name__ == '__main__':
    main()

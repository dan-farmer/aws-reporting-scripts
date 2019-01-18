#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List all AWS resources created by any CloudFormation stack in any region."""

import sys
import csv
import argparse
import boto3
import helpers

def main():
    """Gather and write CSV data, one row per Resource.

    Iterate through specified AWS regions
    Iterate through all CloudFormation stacks
    Iterate through all resources
    Query basic stack and resource information
    """
    args = parse_args()
    if args.region == 'all' or args.region == 'ALL':
        region_list = list(helpers.get_region_list())
    else:
        # Check valid or return default region
        region_list = [helpers.get_region(args.region)]

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    # Get AWS account number from STS
    account_number = boto3.client('sts').get_caller_identity()['Account']

    # Header row
    output.writerow(['Account', 'Region', 'StackName', 'LogicalResourceId', 'ResourceType',
                     'PhysicalResourceId', 'StackID', 'StackStatus'])

    for region in region_list:
        cfn_client = boto3.client('cloudformation', region_name=region)
        stack_status_filter = ['CREATE_IN_PROGRESS',
                               'CREATE_FAILED',
                               'CREATE_COMPLETE',
                               'ROLLBACK_IN_PROGRESS',
                               'ROLLBACK_FAILED',
                               'ROLLBACK_COMPLETE',
                               #'DELETE_IN_PROGRESS',
                               'DELETE_FAILED',
                               #'DELETE_COMPLETE',
                               'UPDATE_IN_PROGRESS',
                               'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                               'UPDATE_COMPLETE',
                               'UPDATE_ROLLBACK_IN_PROGRESS',
                               'UPDATE_ROLLBACK_FAILED',
                               'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                               'UPDATE_ROLLBACK_COMPLETE',
                               'REVIEW_IN_PROGRESS']
        for stack in helpers.get_items(client=cfn_client,
                                       function='list_stacks',
                                       item_name='StackSummaries',
                                       StackStatusFilter=stack_status_filter):
            for resource in helpers.get_items(client=cfn_client,
                                              function='list_stack_resources',
                                              item_name='StackResourceSummaries',
                                              StackName=stack['StackId']):
                try:
                    physical_resource_id = resource['PhysicalResourceId']
                except KeyError:
                    # If a logical resource has no PhysicalResourceId (i.e. ARN), then the
                    # corresponding physical resource does not exist and has been deleted outside
                    # of CloudFormation
                    physical_resource_id = "[Deleted]"
                output.writerow([account_number,
                                 region,
                                 stack['StackName'],
                                 resource['LogicalResourceId'],
                                 resource['ResourceType'],
                                 physical_resource_id,
                                 stack['StackId'],
                                 stack['StackStatus']])

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', type=str, default=False,
                        help='AWS region; Use "all" for all regions')
    return parser.parse_args()

if __name__ == '__main__':
    main()

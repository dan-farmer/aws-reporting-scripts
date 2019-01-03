#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List all AWS resources created by any CloudFormation stack in any region."""

import sys
import csv
import boto3
from helpers import get_regions

def main():
    """Gather and write CSV data, one row per Resource.

    Iterate through available AWS regions
    Iterate through all CloudFormation stacks
    Iterate through all resources
    Query basic stack and resource information
    """

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    # Header row
    output.writerow(['Region', 'StackName', 'LogicalResourceId', 'ResourceType',
                     'PhysicalResourceId', 'StackID', 'StackStatus'])

    for region in get_regions():
        cfn_client = boto3.client('cloudformation', region_name=region)
        for stack in get_stacks(cfn_client):
            for resource in get_resources(cfn_client, stack['StackId']):
                try:
                    physical_resource_id = resource['PhysicalResourceId']
                except KeyError:
                    # If a logical resource has no PhysicalResourceId (i.e. ARN), then the
                    # corresponding physical resource does not exist and has been deleted outside
                    # of CloudFormation
                    physical_resource_id = "[Deleted]"
                output.writerow([region,
                                 stack['StackName'],
                                 resource['LogicalResourceId'],
                                 resource['ResourceType'],
                                 physical_resource_id,
                                 stack['StackId'],
                                 stack['StackStatus']])

def get_stacks(cfn_client):
    """Yield all CloudFormation stacks."""
    next_token = True
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
    while next_token:
        if next_token is not True:
            stack_list = cfn_client.list_stacks(StackStatusFilter=stack_status_filter,
                                                NextToken=next_token)
        else:
            stack_list = cfn_client.list_stacks(StackStatusFilter=stack_status_filter)
        if 'NextToken' in stack_list:
            next_token = stack_list['NextToken']
        else:
            next_token = False
        for stack in stack_list['StackSummaries']:
            yield stack

def get_resources(cfn_client, stack_id):
    """Yield all resources for CloudFormation stack."""
    next_token = True
    while next_token:
        if next_token is not True:
            resource_list = cfn_client.list_stack_resources(StackName=stack_id,
                                                            NextToken=next_token)
        else:
            resource_list = cfn_client.list_stack_resources(StackName=stack_id)
        if 'NextToken' in resource_list:
            next_token = resource_list['NextToken']
        else:
            next_token = False
        for resource in resource_list['StackResourceSummaries']:
            yield resource

if __name__ == '__main__':
    main()

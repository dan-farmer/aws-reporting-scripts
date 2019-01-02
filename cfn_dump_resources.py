#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List all AWS resources created by any CloudFormation stack in any region."""

import sys
import csv
try:
    import boto3
    from helpers import get_regions
except ImportError as err:
    print('ERROR: {0}'.format(err), file=sys.stderr)
    raise err

def main():
    """Gather and write CSV data, one row per Resource.

    Iterate through available AWS regions
    Iterate through all CloudFormation stacks
    Iterate through all resources
    Query basic stack and resource information
    """

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    # Header row
    output.writerow(['Region',
                     'LogicalResourceId',
                     'PhysicalResourceId',
                     'ResourceType',
                     'StackName',
                     'StackID',
                     'StackStatus'])

    for region in get_regions():
        cfn_client = boto3.client('cloudformation', region_name=region)
        for stack in get_stacks(cfn_client):
            for resource in get_resources(cfn_client, stack['StackId']):
                output.writerow([region])

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
    return ''

if __name__ == '__main__':
    main()

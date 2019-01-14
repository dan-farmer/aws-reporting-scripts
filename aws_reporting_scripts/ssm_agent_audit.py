#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List EC2 instances, SSM agent and platform details as CSV."""

import sys
import argparse
import csv
import boto3
import helpers

def main():
    """Gather and write CSV data, one row per Instance.

    Iterate through specified AWS regions
    Iterate through all EC2 instances
    Query basic EC2 instance information (Name tag, EC2 platform)
    Query SSM agent version, status, platform information
    """
    args = parse_args()
    if args.region == 'all' or args.region == 'ALL':
        region_list = list(helpers.get_region_list())
    else:
        # Check valid or return default region
        region_list = [helpers.get_region(args.region)]

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_ALL)

    # Header row
    output.writerow(['Region', 'InstanceID', 'Name', 'EC2Platform', 'SSMPingStatus',
                     'SSMAgentVersion', 'SSMPlatformType', 'SSMPlatformName',
                     'SSMPlatformVersion'])

    for region in region_list:
        ec2_client = boto3.client('ec2', region_name=region)
        ssm_client = boto3.client('ssm', region_name=region)
        for instance in get_instances(ec2_client):
            instance_ssm_info = get_instance_ssm_info(ssm_client, instance['InstanceId'])
            output.writerow([region,
                             instance['InstanceId'],
                             get_instance_name(instance),
                             get_instance_platform(instance),
                             instance_ssm_info['ping_status'],
                             instance_ssm_info['agent_version'],
                             instance_ssm_info['platform_type'],
                             instance_ssm_info['platform_name'],
                             instance_ssm_info['platform_version']])

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', type=str, default=False,
                        help='AWS region; Use "all" for all regions')
    return parser.parse_args()

def get_instances(ec2_client):
    """Yield EC2 instances."""
    next_token = True
    filters = {
        'Name': 'instance-state-name',
        'Values': [
            #'pending',
            'running',
            #'shutting-down',
            #'terminated',
            'stopping',
            'stopped',
        ]
    }
    while next_token:
        if next_token is not True:
            instance_list = ec2_client.describe_instances(Filters=[filters], NextToken=next_token)
        else:
            instance_list = ec2_client.describe_instances(Filters=[filters])
        if 'NextToken' in instance_list:
            next_token = instance_list['NextToken']
        else:
            next_token = False
        for reservation in instance_list['Reservations']:
            for instance in reservation['Instances']:
                yield instance

def get_instance_name(instance):
    """Return instance 'Name' tag value if it exists."""
    instance_name = ''
    try:
        # Looping through tags seems ugly, but no better way in boto3
        # See https://github.com/boto/boto3/issues/264
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
    except KeyError:
        pass    # Instance has no tags at all
    return instance_name

def get_instance_platform(instance):
    """Return instance Platform value if it exists."""
    instance_platform = ''
    try:
        instance_platform = instance['Platform']
    except KeyError:
        pass
    return instance_platform

def get_instance_ssm_info(ssm_client, instance_id):
    """Return SSM agent details."""
    ping_status, agent_version, platform_type, platform_name, platform_version = '', '', '', '', ''
    filters = {'key': 'InstanceIds', 'valueSet': [instance_id]}
    ssm_information = (ssm_client.describe_instance_information
                       (InstanceInformationFilterList=[filters])['InstanceInformationList'])
    if ssm_information:
        ping_status = ssm_information[0]['PingStatus']
        agent_version = ssm_information[0]['AgentVersion']
        platform_type = ssm_information[0]['PlatformType']
        platform_name = ssm_information[0]['PlatformName']
        platform_version = ssm_information[0]['PlatformVersion']
    return {'ping_status': ping_status,
            'agent_version': agent_version,
            'platform_type': platform_type,
            'platform_name': platform_name,
            'platform_version': platform_version}

if __name__ == '__main__':
    main()

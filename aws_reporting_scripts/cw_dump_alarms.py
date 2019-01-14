#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""List AWS CloudWatch alarms.

- Alarm name, Description
- Metric, Stat, Operator, Threshold, Periods number, Period length
- Dimensions (each Name & Value joined)
- First two actions (further actions are ignored)
  - If Action is an SNS topic, proto and endpoints/subscribers
"""

import sys
import argparse
import csv
import boto3
import helpers

def main():
    """Gather and write CSV data, one row per Alarm.

    Iterate through specified AWS regions
    Iterate through all Alarms
    Query for Alarm details
    Iterate through first two returned Alarm Actions
    Test if Actions are SNS topics
    Query for topic name, proto and endpoints
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
    output.writerow(['Account', 'Region',
                     'Name', 'Description',
                     'Metric', 'Stat', 'Op', 'Thresh', 'EvalPeriods', 'Period', 'Dimensions',
                     'Action0', 'Action0 Protocol', 'Action0 Endpoints',
                     'Action1', 'Action1 Protocol', 'Action1 Endpoints'])

    # Get AWS account number from STS
    account_number = boto3.client('sts').get_caller_identity()['Account']

    # Iterate through regions and Alarms
    for region in region_list:
        cw_client = boto3.client('cloudwatch', region_name=region)
        for alarm in get_alarms(cw_client):
            output.writerow([account_number,
                             region])

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', type=str, default=False,
                        help='AWS region; Use "all" for all regions')
    return parser.parse_args()

def get_alarms(cw_client):
    """Yield CloudWatch Alarms."""

def get_topic_name(sns_client, topic):
    """Return DisplayName of SNS topic."""

def get_topic_subscriptions(sns_client, topic):
    """Yield scriptions for SNS topic."""

if __name__ == '__main__':
    main()

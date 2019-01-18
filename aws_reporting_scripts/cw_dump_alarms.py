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
                     'Action0', 'Action0 SNS DisplayName', 'Action0 SNS Subscriptions',
                     'Action1', 'Action1 SNS DisplayName', 'Action1 SNS Subscriptions'])

    # Get AWS account number from STS
    account_number = boto3.client('sts').get_caller_identity()['Account']

    # Iterate through regions and Alarms
    for region in region_list:
        cw_client = boto3.client('cloudwatch', region_name=region)
        for alarm in helpers.get_items(client=cw_client,
                                       function='describe_alarms',
                                       item_name='MetricAlarms'):
            # Join Name and Value for each dimension with '='
            # Then join each dimension pair comma-separated
            dimensions = ','.join(['{}={}'.format(dimension['Name'], dimension['Value'])
                                   for dimension in alarm['Dimensions']])

            # Try getting first two actions
            try:
                action0 = alarm['AlarmActions'][0]
            except IndexError:
                action0 = "No action"
            try:
                action1 = alarm['AlarmActions'][1]
            except IndexError:
                action1 = "No action"

            # Attempt to populate SNS DisplayName and Subscriptions if Actions look like SNS topics
            action0_sns_displayname, action0_sns_subscriptions = '', ''
            action1_sns_displayname, action1_sns_subscriptions = '', ''
            if "arn:aws:sns" in action0 or "arn:aws:sns" in action1:
                sns_client = boto3.client('sns', region_name=region)
                # Join proto and endpoint for each subscription ': '
                # Then join each subscription pair comman-separated
                if "arn:aws:sns" in action0:
                    action0_sns_displayname = get_topic_name(sns_client, action0)
                    action0_sns_subscriptions = ','.join(
                        ['{}: {}'.format(subscription['Protocol'],
                                         subscription['Endpoint'])
                         for subscription in helpers.get_items(client=sns_client,
                                                               function='list_subscriptions_by_topic',
                                                               item_name='Subscriptions',
                                                               TopicArn=action0)])
                if "arn:aws:sns" in action1:
                    action0_sns_subscriptions = ','.join(
                        ['{}: {}'.format(subscription['Protocol'],
                                         subscription['Endpoint'])
                         for subscription in helpers.get_items(client=sns_client,
                                                               function='list_subscriptions_by_topic',
                                                               item_name='Subscriptions',
                                                               TopicArn=action0)])

            # Output data
            output.writerow([account_number,
                             region,
                             alarm['AlarmName'],
                             alarm.get('AlarmDescription', ''),
                             alarm['MetricName'],
                             pretty_statistic(alarm['Statistic']),
                             pretty_operator(alarm['ComparisonOperator']),
                             alarm['Threshold'],
                             alarm['EvaluationPeriods'],
                             alarm['Period'],
                             dimensions,
                             action0,
                             action0_sns_displayname,
                             action0_sns_subscriptions,
                             action1,
                             action1_sns_displayname,
                             action1_sns_subscriptions])

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', type=str, default=False,
                        help='AWS region; Use "all" for all regions')
    return parser.parse_args()

def pretty_statistic(stat):
    """Return a pretty/abbreviated version of statistic."""
    translation = {"Average": "avg",
                   "Maximum": "max",
                   "Minimum": "min"}
    try:
        stat = translation[stat]
    except KeyError:
        pass
    return stat

def pretty_operator(operator):
    """Return a pretty/abbreviated version of operator."""
    translation = {"GreaterThanOrEqualToThreshold": ">=",
                   "GreaterThanThreshold": ">",
                   "LessThanOrEqualToThreshold": "<=",
                   "LessThanThreshold": "<"}
    try:
        operator = translation[operator]
    except KeyError:
        pass
    return operator

def get_topic_name(sns_client, topic):
    """Return DisplayName of SNS topic."""
    displayname = ''
    response = sns_client.get_topic_attributes(TopicArn=topic)
    try:
        displayname = response['Attributes']['DisplayName']
    except KeyError:
        pass # No DisplayName
    return displayname

if __name__ == '__main__':
    main()

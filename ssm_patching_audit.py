#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""
List SSM Maintenance Windows, Tasks and Patching Baseline details.

- Maintenance Window schedule etc
- First returned Maintenance Window Task (further tasks are ignored)
  - Basic details
  - Target Patch Group
  - Task
  - Task operation
  - Patch Baseline
    - Patch Baseline name
    - Patch Baseline OS
    - Patch Filter (MSRC Severity)
    - Patch Filter (Classification)
    - Approval Delay
"""

import sys
import csv
try:
    import boto3
    import botocore.exceptions
except ImportError as err:
    print('ERROR: {0}'.format(err), file=sys.stderr)
    raise err

def main():
    """Gather and write CSV data, one row per Maintenance Window.

    Iterate through available AWS regions
    Iterate through all SSM Maintenance Windows
    Query for first Maintenance Window Task
    Query for associated Task, Patch Group and Patch Baseline details
    """

    output = csv.writer(sys.stdout, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_ALL)

    # Header row
    output.writerow(['Account',
                     'Region',
                     'MW ID',
                     'MW Name',
                     'MW Schedule',
                     'MW TZ',
                     'Task 1 ID',
                     'Patch Group',
                     'Task',
                     'Operation',
                     'Baseline',
                     'Baseline Name',
                     'OS',
                     'Patch Filter (MSRC Sev)',
                     'Patch Filter (Class)',
                     'Approval Delay'])

    #Iterate through regions and Maintenance Windows
    for region in get_regions():
        ssm_client = boto3.client('ssm', region_name=region)
        for maint_window_id in get_maintenance_windows(ssm_client):

            #Gather data
            maint_window_info = get_maint_window_info(ssm_client, maint_window_id)
            task_id = get_maint_window_task(ssm_client, maint_window_id)
            task_info = get_task_info(ssm_client, maint_window_id, task_id)
            patch_tag = get_target_patch_tag(ssm_client, maint_window_id, task_info[0])
            baseline_id = get_baseline_id(ssm_client, patch_tag)
            baseline_info = get_baseline_info(ssm_client, baseline_id)

            #Output data
            output.writerow([boto3.client('sts').get_caller_identity()['Account'],
                             region,
                             maint_window_id,
                             maint_window_info[0],  #Name
                             maint_window_info[1],  #Sched
                             maint_window_info[2],  #TZ
                             task_id,               #First returned MW Task ID
                             patch_tag,             #Patch Group
                             task_info[1],          #Task
                             task_info[2],          #Operation
                             baseline_id,           #Baseline
                             baseline_info[0],      #Name
                             baseline_info[1],      #OS
                             baseline_info[2],      #Patch Filter (MSRC Sev)
                             baseline_info[3],      #Patch Filter (Class)
                             baseline_info[4]])     #Approval Delay

def get_regions():
    """Return list of AWS regions."""
    try:
        ec2_client = boto3.client('ec2')
    except botocore.exceptions.NoRegionError:
        # If we fail because the user has no default region, use us-east-1
        # This is for listing regions only
        # Iterating Maintenance Windows is then performed in each region
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

def get_maintenance_windows(ssm_client):
    """Yield SSM Maintenance Windows."""
    next_token = True
    filters = {'Key':'Enabled', 'Values':['true']}
    while next_token:
        if next_token is not True:
            maint_window_list = ssm_client.describe_maintenance_windows(
                Filters=[filters],
                NextToken=next_token)
        else:
            maint_window_list = ssm_client.describe_maintenance_windows(
                Filters=[filters])
        if 'NextToken' in maint_window_list:
            next_token = maint_window_list['NextToken']
        else:
            next_token = False
        for window in maint_window_list['WindowIdentities']:
            yield window['WindowId']

def get_maint_window_info(ssm_client, maint_window_id):
    """Return basic parameters of Maintenance Window."""
    name, sched, time_zone = '', '', ''
    maint_window = ssm_client.get_maintenance_window(WindowId=maint_window_id)
    name = maint_window['Name']
    sched = maint_window['Schedule']
    try:
        time_zone = maint_window['ScheduleTimezone']
    except KeyError:
        pass     #ScheduleTimezone is not set
    return name, sched, time_zone

def get_maint_window_task(ssm_client, maint_window_id):
    """Return ID of first Maintenance Window Task in Maintenance Window."""
    task_id = ''
    task_list = ssm_client.describe_maintenance_window_tasks(
        WindowId=maint_window_id,
        MaxResults=10)
    try:
        task_id = task_list['Tasks'][0]['WindowTaskId']
    except IndexError:
        pass    #No Task exists for this Maintenance Window
    return task_id

def get_task_info(ssm_client, maint_window_id, task_id):
    """Return Target ID, Task and Operation of Maintenance Window Task."""
    target_id, task, operation = '', '', ''
    if task_id:
        maint_window_task = ssm_client.get_maintenance_window_task(
            WindowId=maint_window_id,
            WindowTaskId=task_id)

        target_id = next(item for item in maint_window_task['Targets']
                         if item['Key'] == 'WindowTargetIds')['Values'][0]
        task = maint_window_task['TaskArn']
        try:
            operation = (maint_window_task['TaskInvocationParameters']
                         ['RunCommand']['Parameters']['Operation'][0])
        except (KeyError, IndexError):
            pass    #No 'Operation' parameter or values set for task
    return target_id, task, operation

def get_target_patch_tag(ssm_client, maint_window_id, target_id):
    """Return 'Patch Group' tag value of Maintenance Window Target."""
    patch_tag = ''
    filters = {'Key':'WindowTargetId', 'Values':[target_id]}
    if target_id:
        try:
            target_list = ssm_client.describe_maintenance_window_targets(
                WindowId=maint_window_id,
                Filters=[filters])
        except KeyError:
            pass    #No targets
        try:
            patch_tag = next(item for item in target_list['Targets'][0]['Targets']
                             if item['Key'] == 'tag:Patch Group')['Values'][0]
        except (KeyError, IndexError):
            pass    #No 'Patch Group' tag
    return patch_tag

def get_baseline_id(ssm_client, patch_tag):
    """Return ID of Patch Baseline for Patch Group."""
    baseline_id = ''
    if patch_tag:
        baseline = ssm_client.get_patch_baseline_for_patch_group(PatchGroup=patch_tag)
        baseline_id = baseline['BaselineId']
    return baseline_id

def get_baseline_info(ssm_client, baseline_id):
    """Return Patch Baseline properties."""
    name, operating_system, filter_msrc_sev, filter_class, delay = '', '', '', '', ''
    if baseline_id:
        baseline = ssm_client.get_patch_baseline(BaselineId=baseline_id)
        name = baseline['Name']
        operating_system = baseline['OperatingSystem']
        patch_filters = (baseline['ApprovalRules']['PatchRules']
                         [0]['PatchFilterGroup']['PatchFilters'])
        filter_msrc_sev = next(item for item in patch_filters
                               if item['Key'] == 'MSRC_SEVERITY')['Values'][0]
        filter_class = ",".join(next(item for item in patch_filters
                                     if item['Key'] == 'CLASSIFICATION')['Values'])
        delay = baseline['ApprovalRules']['PatchRules'][0]['ApproveAfterDays']
    return name, operating_system, filter_msrc_sev, filter_class, delay

if __name__ == '__main__':
    main()

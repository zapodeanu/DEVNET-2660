#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Gabriel Zapodeanu PTME"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import json
import logging
import os
import time
import yaml
import base64
import requests
import argparse


from datetime import datetime
from dnacentersdk import DNACenterAPI, ApiError
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth

load_dotenv('environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')


os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This application will automate provisioning or re-provisioning of a network device using Catalyst Center APIs.
    The device re-provisioning is supported only if at the same site
    :param hostname: device hostname that will be provisioned or re-provisioned
    :param site_hierarchy: the Catalyst Center site hierarchy where the device will be provisioned
    :return:
    """

    # logging basic
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('  App "provision_wired_device.py" run start, ' + current_time)

    # parse the input arguments
    parser = argparse.ArgumentParser(description="A script that accepts two arguments.")
    parser.add_argument("hostname", help="The device hostname")
    parser.add_argument("site_hierarchy", help="The site hierarchy where the device will be provisioned")

    args = parser.parse_args()
    hostname = args.hostname
    site_hierarchy = args.site_hierarchy

    logging.info('  Device hostname: ' + hostname)
    logging.info('  Site hierarchy: ' + site_hierarchy)

    # create a CCenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CC_USER, password=CC_PASS, base_url=CC_URL, version='2.3.7.6',
                            verify=False)

    # get the device management IP address

    response = catalyst_center_api.devices.get_device_list(hostname=hostname)
    management_ip_address = response['response'][0]['managementIpAddress']
    device_id = response['response'][0]['id']
    logging.info('  Device management IP address is: ' + management_ip_address)

    # check if device is already provisioned
    response = catalyst_center_api.sda.get_provisioned_devices(network_device_id=device_id)

    try:
        if response['response'] == []:
            provisioned = False
        else:
            provisioned = True
    except ApiError as e:
        error_message = str(e)
        logging.info('  Device not found')

    if not provisioned:
        # provision device to site
        logging.info('  Device not provisioned, starting provisioning to new site')
        response = catalyst_center_api.sda.provision_wired_device(deviceManagementIpAddress=management_ip_address,
                                                                  siteNameHierarchy=site_hierarchy)
        status = response['status']
        task_url = response['taskStatusUrl']
        task_id = response['taskId']

        logging.info('  Provisioning Task Status: ' + status)
        logging.info('  Provisioning Task URL: ' + task_url)

        # check device provisioning status
        completed = False
        while completed is False:
            time.sleep(5)
            response = catalyst_center_api.task.get_task_by_id(task_id=task_id)
            if response['endTime'] != '':
                completed = True
        if response['isError'] is True:
            provisioning_status = 'Device provisioned failed, check task url: ' + task_url
        else:
            provisioning_status = 'Device provisioned successfully to site'

    else:
        # re-provision device to the same location
        logging.info('  Device already provisioned, starting re-provisioning to site')

        response = catalyst_center_api.sda.re_provision_wired_device_v1(deviceManagementIpAddress=management_ip_address,
                                                                        siteNameHierarchy=site_hierarchy)
        status = response['status']
        provisioning_status = response['description']

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info('  ' + provisioning_status)
    logging.info('  App "provision_wired_device.py" run end: ' + date_time)
    return provisioning_status


if __name__ == '__main__':
    main()
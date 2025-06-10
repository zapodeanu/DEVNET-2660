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

__author__ = "Gabriel Zapodeanu Principal TME"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import json
import logging
import os
import time
import argparse

from datetime import datetime
from catalystcentersdk import CatalystCenterAPI
from dotenv import load_dotenv

load_dotenv('../environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')
CREDENTIALS = os.getenv('CREDENTIALS')

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This application add a device to the inventory. It will use the Catalyst Center credentials already configured.
    :param device_ip_address: the device IP address that will be used by Catalyst Center to manage the device
    :return: none
    """

    # logging basic
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('  App "add_device.py" run start, ' + current_time)

    # parse the input argument
    parser = argparse.ArgumentParser(description="A script that accepts one argument.")
    parser.add_argument("device_ip_address", help="The device management IP address")

    args = parser.parse_args()
    device_ip_address = args.device_ip_address

    credentials = json.loads(CREDENTIALS)
    logging.info('  Device credentials found')

    # update the httpSecure param as boolean, not string as imported from .env file
    credentials['httpSecure'] = False

    # create a CatalystCenterAPI "Connection Object" to use the Python SDK
    cc_api = CatalystCenterAPI(username=CC_USER, password=CC_PASS, base_url=CC_URL, version='2.3.7.9',
                            verify=False)

    # verify if device already managed by Catalyst Center
    response = cc_api.devices.get_device_list(management_ip_address=device_ip_address)
    if response['response'] != []:
        logging.info('  The device is already managed by Catalyst Center')
        return

    # add device to inventory
    logging.info('  The device is not managed by Catalyst Center. Add device process started')
    logging.info('  The device will be managed with the IP address: ' + device_ip_address)
    payload = credentials | {
        "ipAddress": [
            "10.93.141.22"
        ],
        "type": "NETWORK_DEVICE"
    }

    response = cc_api.devices.add_device(payload=payload)
    task_id = response['response']['taskId']
    logging.info('  The add device task Id is:' + task_id)

    # check task completion
    time.sleep(5)
    status = 'PENDING'
    while status == 'PENDING':
        response = cc_api.task.get_tasks_by_id(id=task_id)
        status = response['response']['status']
        time.sleep(5)

    result_location = CC_URL + response['response']['resultLocation']
    logging.info('  The add device task completed: ' + status)
    logging.info('  Details may be found here: ' + result_location)

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info('  App "add_device.py" run end: ' + date_time)
    return


if __name__ == '__main__':
    main()

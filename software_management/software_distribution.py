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

from pprint import pprint
from datetime import datetime
from dnacentersdk import DNACenterAPI, ApiError
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth

load_dotenv('environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')
GITHUB_USERNAME = 'zapodeanu'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

GITHUB_REPO = 'dnacenter_day_n_inventory'

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This application will distribute the golden image to the device with the provided hostname.
    The image distribution will start immediately.
    :return:
    """

    # logging basic
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('  App "software_distribution.py" run start, ' + current_time)

    # parse the input arguments
    parser = argparse.ArgumentParser(description="A script that accepts one argument.")
    parser.add_argument("hostname", help="The network device hostname")

    args = parser.parse_args()
    hostname = args.hostname

    logging.info('  Device hostname: ' + hostname)

    # create a CCenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CC_USER, password=CC_PASS, base_url=CC_URL, version='2.3.7.6',
                            verify=False)

    # get the device unique identifier

    response = catalyst_center_api.devices.get_device_list(hostname=hostname)
    if response['response'] == []:
        # device does not exist
        image_distribution_status = '  Catalyst Center does not manage the device ' + hostname
    else:
        # device found
        device_id = response['response'][0]['id']
        logging.info('  Device uuid is: ' +device_id)
        # trigger image distribution
        payload = [
            {
                "deviceUuid": device_id
            }
        ]
        response = catalyst_center_api.software_image_management_swim.trigger_software_image_distribution(payload=payload)
        task_id = response['response']['taskId']
        logging.info('  Image distribution task id is: ' + task_id)

        # check task completion
        time.sleep(10)
        status = 'PENDING'
        while status == 'PENDING':
            response = catalyst_center_api.task.get_tasks_by_id(id=task_id)
            status = response['response']['status']
            time.sleep(10)
        if status == 'SUCCESS':
            image_distribution_status = '  Image distribution completed successfully for device: ' + hostname
        else:
            image_distribution_status = '  Image distribution failed for device: ' + hostname + ', for details call API: https://' + CC_URL + '/dna/intent/api/v1/tasks/' + task_id + '/detail'

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info(' ' + image_distribution_status)
    logging.info('  App "software_distribution.py" run end: ' + date_time)
    return image_distribution_status


if __name__ == '__main__':
    main()
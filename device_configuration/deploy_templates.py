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

__author__ = "Gabriel Zapodeanu TME, ENB"
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
from dnacentersdk import DNACenterAPI
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth

load_dotenv('../environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')
CREDENTIALS = os.getenv('CREDENTIALS')

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This script will load the file with the name {file_info}
    The file includes the information required to deploy the template. The network device hostname, the Catalyst Center
    project name, the configuration template file name.
    The application will:
     - verify if the project exists and create a new project, if not
     - update or upload the configuration template
     - commit the template
     - verify the device hostname is valid, and reachable
     - deploy the template
     - verify completion and status of the template deployment
    """

    # logging, debug level, to file {application_run.log}
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('App "deploy_templates.py" Start, ' + current_time)

    # templates folder path
    project_details_path = Path(__file__).parent/'../templates_jenkins/project_details.yml'

    with open(project_details_path, 'r') as file:
        project_data = yaml.safe_load(file)

    dnac_url = 'https://' + project_data['dna_center']['ip_address']
    dnac_user = project_data['dna_center']['username']
    dnac_pass = project_data['dna_center']['password']

    project_name = project_data['project']['name']
    template_file = project_data['template']['name']
    template_name = template_file.split('.')[0]

    devices_list = project_data['devices_info']['hostname']

    # Create a DNACenterAPI "Connection Object"
    dnac_api = DNACenterAPI(username=dnac_user, password=dnac_pass, base_url=dnac_url, version='2.2.2.3', verify=False)

    # check if existing project, if not create a new project
    response = dnac_api.configuration_templates.get_projects(name=project_name)
    if response == []:
        # project does not exist, create project
        payload_data = {'name': project_name}
        response = dnac_api.configuration_templates.create_project(payload=payload_data)
        time.sleep(15)
        response = dnac_api.configuration_templates.get_projects(name=project_name)

    project_id = response[0]['id']
    logging.info('Project name: ' + project_name)
    logging.info('Project id: ' + project_id)

    # verify if template exist, delete if it does
    response = dnac_api.configuration_templates.get_projects(name=project_name)
    templates_list = response[0]['templates']
    template_id = None
    for template in templates_list:
        if template['name'] == template_name:
            template_id = template['id']

    if template_id is not None:
        response = dnac_api.configuration_templates.deletes_the_template(template_id=template_id)
        logging.info('Template found and deleted')
        time.sleep(15)

    # create the new CLI template
    template_file_path = Path(__file__).parent/'../templates_jenkins/cli_template.txt'
    cli_file = open(template_file_path, 'r')  # open file with the template
    cli_config_commands = cli_file.read()  # read the file

    payload_template = payload = {
        "name": template_name,
        "tags": [],
        "author": "Jenkins",
        "deviceTypes": [
            {
                "productFamily": "Routers"
            },
            {
                "productFamily": "Switches and Hubs"
            }
        ],
        "softwareType": "IOS-XE",
        "softwareVariant": "XE",
        "softwareVersion": "",
        "templateContent": cli_config_commands,
        "rollbackTemplateContent": "",
        "rollbackTemplateParams": [],
        "parentTemplateId": project_id,
        "templateParams": []
    }
    response = dnac_api.configuration_templates.create_template(project_id=project_id,payload=payload_template)
    task_id = response['response']['taskId']
    logging.info('Created template with the name: ' + template_name)
    time.sleep(15)

    # check the task result
    response = dnac_api.configuration_templates.get_projects(name=project_name)
    templates_list = response[0]['templates']
    template_id = None
    for template in templates_list:
        if template['name'] == template_name:
            template_id = template['id']

    # commit the template
    commit_payload = {
        'comments': 'Jenkins committed',
        'templateId': template_id
    }
    response = dnac_api.configuration_templates.version_template(payload=commit_payload)
    logging.info('Template committed')
    time.sleep(5)

    # deploy the CLI templates
    deployment_report_info = []
    for device in devices_list:
        deploy_payload = {
            "templateId": template_id,
            "forcePushTemplate": True,
            "targetInfo": [
                {
                    "id": device,
                    "type": "MANAGED_DEVICE_HOSTNAME"
                }
            ]
        }
        response = dnac_api.configuration_templates.deploy_template_v2(payload=deploy_payload)
        task_id = response['response']['taskId']
        logging.info('Deploying template to device: ' + device)
        time.sleep(15)

        # retrieve the deployment status
        response = dnac_api.task.get_task_by_id(task_id=task_id)
        deployment_status = response['response']['isError']
        if deployment_status is False:
            deployment_report_info.append(
                {'hostname': device, 'status': 'successful'}
            )
        else:
            deployment_report_info.append(
                {'hostname': device, 'status': 'not successful'}
            )

    # save deployment report to file
    deployment_report = {
        'timestamp': current_time,
        'template_content': cli_config_commands,
        'report': deployment_report_info}
    report_file_path = Path(__file__).parent/'../templates_jenkins/deployment_report.json'
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(deployment_report))

    logging.info('Deployment Report:')
    logging.info(json.dumps(deployment_report))

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info('End of Application "deploy_templates.py" Run: ' + date_time)
    return


if __name__ == "__main__":
    main()

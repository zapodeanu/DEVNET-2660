
# This plan will distribute the golden software image to the devices from the
# user provided "non_compliant_devices.json" file


# Terraform provider required by the plan
terraform {
  required_providers {
    catalystcenter = {
      source = "cisco-en-programmability/catalystcenter"
      version = "1.1.1-beta"
    }
  }
}

# Configure provider with your Catalyst Center credentials
provider "catalystcenter" {
  username   = var.CC_USER
  password   = var.CC_PASS
  base_url   = var.CC_URL
  debug      = "false"
  ssl_verify = "false"
}

# Import the software non-compliant devices file
locals {
  # get json
  non_compliant_devices_list = jsondecode(file("non_compliant_devices.json"))
}

# Define the software "distribution" module that will be called for each device
module "swim_upgrade" {
  source    = "./modules/distribution"
  count = length(local.non_compliant_devices_list)
  device_info = local.non_compliant_devices_list[count.index]
}

# Output the devices hostname requiring an image upgrade
output "devices_upgraded" {
  description = "Device Hostname"
  value = [for device in local.non_compliant_devices_list :
  device.device_name]
}

# Detailed device information from "distribution" module
output "device_upgrade_details" {
  description = "Detailed information for each device being upgraded"
  value = [for module in module.swim_upgrade : module.device_details]
}

# Task information from "distribution" module
output "upgrade_tasks" {
  description = "Software Distribution Task Id and status"
  value = [for module in module.swim_upgrade : module.task_status]
}




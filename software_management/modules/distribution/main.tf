
# The "distribution" module will be called, once for every device to be upgraded
terraform {
  required_providers {
    catalystcenter = {
      version = "1.1.1-beta"
      source  = "cisco-en-programmability/catalystcenter"
    }
  }
}

variable "device_info" {
  description = "Software non-compliant device info"
  type        = map(string)
}

# Get the device details for the device with the provided hostname
data "catalystcenter_network_device_list" "response" {
  hostname = [var.device_info.device_name]
}

# Use the image distribution resource, provide the device id
resource "catalystcenter_image_distribution" "response" {
  provider = catalystcenter
  lifecycle {
    create_before_destroy = true
  }
  parameters {
    payload {
      device_uuid = data.catalystcenter_network_device_list.response.items[0].id
    }
  }
}

# Verify the software distribution task status
data "catalystcenter_task" "task_response" {
  depends_on = [catalystcenter_image_distribution.response]
  provider   = catalystcenter
  task_id    = catalystcenter_image_distribution.response.item[0].task_id
}

# Outputs with details about upgraded devices
output "device_details" {
    description = "Detailed device information and upgrade status"
      value = {
        device_name = var.device_info.device_name
        device_id = data.catalystcenter_network_device_list.response.items[0].id
        current_software_version = data.catalystcenter_network_device_list.response.items[0].software_version
        platform_id = data.catalystcenter_network_device_list.response.items[0].platform_id
    }
  }

# Outputs with software distribution task id details
output "task_status" {
  description = "Task monitoring information"
  value = {
    task_id = catalystcenter_image_distribution.response.item[0].task_id
    device_name = var.device_info.device_name
  }
}



output "foundation_defaults" {
  description = "Generated defaults that later guest modules should inherit."
  value       = local.foundation_defaults
}

output "hosts" {
  description = "Generated host topology for the environment."
  value       = var.proxmox_hosts
}

output "cluster_template" {
  description = "homelab-core template metadata."
  value = {
    vm_id = proxmox_virtual_environment_vm.ubuntu_2404_template.vm_id
    name  = proxmox_virtual_environment_vm.ubuntu_2404_template.name
  }
}

output "containers" {
  description = "Provisioned LXC container topology."
  value = {
    for name, ct in proxmox_virtual_environment_container.containers : name => {
      ct_id = ct.vm_id
      name  = name
    }
  }
}

output "cluster_nodes" {
  description = "Provisioned homelab-core guest topology."
  value = {
    for name, node in proxmox_virtual_environment_vm.cluster_nodes : name => {
      vm_id              = node.vm_id
      name               = node.name
      management_address = var.cluster_nodes[name].management_address
    }
  }
}

output "home_assistant" {
  description = "Provisioned Home Assistant guest topology."
  value = {
    vm_id              = proxmox_virtual_environment_vm.home_assistant.vm_id
    name               = proxmox_virtual_environment_vm.home_assistant.name
    management_address = var.home_assistant.management_address
    mac_address        = var.home_assistant.mac_address
  }
}

output "openclaw_gateways" {
  description = "Provisioned OpenClaw gateway guest topology."
  value = {
    for name, gateway in proxmox_virtual_environment_vm.openclaw_gateways : name => {
      vm_id              = gateway.vm_id
      name               = gateway.name
      management_address = var.openclaw_gateways[name].management_address
      mac_address        = var.openclaw_gateways[name].mac_address
      bot_slug           = var.openclaw_gateways[name].bot_slug
    }
  }
}

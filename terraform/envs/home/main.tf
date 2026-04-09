locals {
  foundation_defaults = {
    node_name          = var.proxmox_node_name
    pool_id            = var.proxmox_pool_id
    bridge_name        = var.proxmox_bridge_name
    vm_disk_storage    = var.proxmox_vm_disk_storage
    iso_storage        = var.proxmox_iso_storage
    snippet_storage    = var.proxmox_snippet_storage
    template_storage   = var.proxmox_template_storage
    management_cidr    = var.proxmox_management_cidr
    management_gateway = var.proxmox_management_gateway
  }

  # LXC template IDs reference pre-existing templates on the local (file-based)
  # datastore. The bpg/proxmox download_file resource cannot import or adopt
  # pre-existing files, so we compute the ID directly and require the template
  # to exist on the node before applying.
  container_template_file_ids = {
    for k, v in var.containers : k => "${var.proxmox_iso_storage}:vztmpl/${v.template_file_name}"
  }
}

resource "proxmox_virtual_environment_pool" "homelab_pool" {
  pool_id = var.proxmox_pool_id
  comment = "AI Homelab managed guests on ${var.proxmox_node_name}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "proxmox_download_file" "ubuntu_2404_cloud_image" {
  content_type = "import"
  datastore_id = var.proxmox_iso_storage
  file_name    = var.cluster_template.image_file_name
  node_name    = var.proxmox_node_name
  overwrite    = false
  url          = var.cluster_template.image_url
}

resource "proxmox_virtual_environment_vm" "ubuntu_2404_template" {
  name        = var.cluster_template.name
  description = "Ubuntu 24.04 cloud image template for homelab guests"
  tags        = ["homelab", "template", "ubuntu-2404", "terraform"]

  node_name = var.proxmox_node_name
  pool_id   = proxmox_virtual_environment_pool.homelab_pool.pool_id
  vm_id     = var.cluster_template.vm_id

  bios          = "ovmf"
  machine       = "q35"
  scsi_hardware = "virtio-scsi-single"
  on_boot       = false
  started       = false
  tablet_device = false
  template      = true

  agent {
    enabled = true
    trim    = true
  }

  cpu {
    cores   = 2
    sockets = 1
    type    = "x86-64-v2-AES"
  }

  memory {
    dedicated = 2048
    floating  = 2048
  }

  efi_disk {
    datastore_id      = var.proxmox_template_storage
    type              = "4m"
    pre_enrolled_keys = true
  }

  disk {
    datastore_id = var.proxmox_template_storage
    import_from  = proxmox_download_file.ubuntu_2404_cloud_image.id
    interface    = "scsi0"
    discard      = "on"
    iothread     = true
    size         = var.cluster_template.disk_gb
    ssd          = true
  }

  network_device {
    bridge = var.proxmox_bridge_name
    model  = "virtio"
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  vga {
    type = "serial0"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "proxmox_virtual_environment_vm" "home_assistant" {
  name        = var.home_assistant.name
  description = var.home_assistant.description
  tags        = sort(var.home_assistant.tags)

  node_name = var.proxmox_node_name
  pool_id   = proxmox_virtual_environment_pool.homelab_pool.pool_id
  vm_id     = var.home_assistant.vm_id

  bios                = "ovmf"
  machine             = "q35"
  scsi_hardware       = "virtio-scsi-single"
  on_boot             = var.home_assistant.start_on_boot
  started             = true
  tablet_device       = false
  reboot_after_update = false

  agent {
    enabled = true
    trim    = true
  }

  cpu {
    cores   = var.home_assistant.cpu_cores
    sockets = 1
    type    = "x86-64-v2-AES"
  }

  memory {
    dedicated = var.home_assistant.memory_mb
    floating  = var.home_assistant.memory_mb
  }

  efi_disk {
    datastore_id      = var.home_assistant.datastore_id
    type              = "2m"
    pre_enrolled_keys = false
  }

  disk {
    datastore_id = var.home_assistant.datastore_id
    interface    = "scsi0"
    cache        = "writethrough"
    discard      = "on"
    iothread     = true
    size         = var.home_assistant.disk_gb
    ssd          = true
  }

  network_device {
    bridge      = var.proxmox_bridge_name
    model       = "virtio"
    mac_address = var.home_assistant.mac_address
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  vga {
    type = "serial0"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "proxmox_virtual_environment_container" "containers" {
  for_each = var.containers

  description   = "Tailscale appliance managed by Terraform"
  tags          = sort(["homelab", "tailscale", "appliance", "terraform"])
  node_name     = var.proxmox_node_name
  pool_id       = proxmox_virtual_environment_pool.homelab_pool.pool_id
  vm_id         = each.value.ct_id
  unprivileged  = each.value.unprivileged
  start_on_boot = each.value.start_on_boot
  started       = each.value.start_on_boot

  operating_system {
    template_file_id = local.container_template_file_ids[each.key]
    type             = "debian"
  }

  cpu {
    cores = each.value.cpu_cores
  }

  memory {
    dedicated = each.value.memory_mb
    swap      = each.value.swap_mb
  }

  disk {
    datastore_id = var.proxmox_vm_disk_storage
    size         = each.value.disk_gb
  }

  features {
    nesting = each.value.nesting
  }

  network_interface {
    name   = "eth0"
    bridge = var.proxmox_bridge_name
  }

  initialization {
    hostname = each.key

    dns {
      domain  = var.proxmox_management_domain
      servers = var.proxmox_management_dns_servers
    }

    ip_config {
      ipv4 {
        address = each.value.management_cidr
        gateway = var.proxmox_management_gateway
      }
    }

    user_account {
      keys = [trimspace(var.cluster_operator_ssh_public_key)]
    }
  }

  lifecycle {
    ignore_changes  = [description]
    prevent_destroy = true
  }
}

resource "proxmox_virtual_environment_vm" "cluster_nodes" {
  for_each = var.cluster_nodes

  name        = each.key
  description = "homelab-core ${each.value.role} managed by Terraform"
  tags        = ["homelab", "homelab-core", each.value.role, "terraform"]

  node_name = var.proxmox_node_name
  pool_id   = proxmox_virtual_environment_pool.homelab_pool.pool_id
  vm_id     = each.value.vm_id

  bios          = "ovmf"
  machine       = "q35"
  scsi_hardware = "virtio-scsi-single"
  on_boot       = true
  started       = true
  tablet_device = false

  clone {
    vm_id        = proxmox_virtual_environment_vm.ubuntu_2404_template.vm_id
    datastore_id = var.proxmox_vm_disk_storage
    full         = true
    node_name    = var.proxmox_node_name
    retries      = 3
  }

  agent {
    enabled = true
    trim    = true
  }

  cpu {
    cores   = each.value.cpu_cores
    sockets = 1
    type    = "x86-64-v2-AES"
  }

  memory {
    dedicated = each.value.memory_mb
    floating  = each.value.memory_mb
  }

  initialization {
    datastore_id = var.proxmox_template_storage
    interface    = "ide2"

    dns {
      domain  = var.proxmox_management_domain
      servers = var.proxmox_management_dns_servers
    }

    ip_config {
      ipv4 {
        address = each.value.management_cidr
        gateway = var.proxmox_management_gateway
      }
    }

    user_account {
      keys     = [trimspace(var.cluster_operator_ssh_public_key)]
      username = var.cluster_operator_user
    }
  }

  disk {
    datastore_id = var.proxmox_vm_disk_storage
    interface    = "scsi0"
    discard      = "on"
    iothread     = true
    size         = each.value.disk_gb
    ssd          = true
  }

  network_device {
    bridge = var.proxmox_bridge_name
    model  = "virtio"
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  vga {
    type = "serial0"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "proxmox_virtual_environment_vm" "openclaw_gateways" {
  for_each = var.openclaw_gateways

  name        = each.key
  description = "OpenClaw gateway for bot ${each.value.bot_slug} managed by Terraform"
  tags        = ["gateway", "homelab", "openclaw", "terraform"]

  node_name = var.proxmox_node_name
  pool_id   = proxmox_virtual_environment_pool.homelab_pool.pool_id
  vm_id     = each.value.vm_id

  bios          = "ovmf"
  machine       = "q35"
  scsi_hardware = "virtio-scsi-single"
  on_boot       = each.value.start_on_boot
  started       = true
  tablet_device = false

  clone {
    vm_id        = proxmox_virtual_environment_vm.ubuntu_2404_template.vm_id
    datastore_id = var.proxmox_vm_disk_storage
    full         = true
    node_name    = var.proxmox_node_name
    retries      = 3
  }

  agent {
    enabled = true
    trim    = true
  }

  cpu {
    cores   = each.value.cpu_cores
    sockets = 1
    type    = "x86-64-v2-AES"
  }

  memory {
    dedicated = each.value.memory_mb
    floating  = each.value.memory_mb
  }

  initialization {
    datastore_id = var.proxmox_template_storage
    interface    = "ide2"

    dns {
      domain  = var.proxmox_management_domain
      servers = var.proxmox_management_dns_servers
    }

    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }

    user_account {
      keys     = [trimspace(var.cluster_operator_ssh_public_key)]
      username = var.cluster_operator_user
    }
  }

  disk {
    datastore_id = var.proxmox_vm_disk_storage
    interface    = "scsi0"
    discard      = "on"
    iothread     = true
    size         = each.value.disk_gb
    ssd          = true
  }

  network_device {
    bridge      = var.proxmox_bridge_name
    mac_address = each.value.mac_address
    model       = "virtio"
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  vga {
    type = "serial0"
  }

  lifecycle {
    ignore_changes  = [initialization[0].user_account[0].keys]
    prevent_destroy = true
  }
}

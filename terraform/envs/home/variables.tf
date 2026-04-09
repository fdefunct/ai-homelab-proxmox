variable "proxmox_endpoint" {
  description = "Proxmox API endpoint for the environment."
  type        = string

  validation {
    condition = (
      length(trimspace(var.proxmox_endpoint)) > 0 &&
      can(regex("^https://", var.proxmox_endpoint))
    )
    error_message = "proxmox_endpoint must be a non-empty HTTPS URL."
  }
}

variable "proxmox_insecure" {
  description = "Whether to skip TLS verification for the Proxmox API endpoint."
  type        = bool
}

variable "proxmox_node_name" {
  description = "Primary Proxmox node name for the environment."
  type        = string
}

variable "proxmox_pool_id" {
  description = "Default Proxmox pool identifier reserved for AI Homelab guests."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_pool_id)) > 0
    error_message = "proxmox_pool_id must be a non-empty string."
  }
}

variable "proxmox_vm_disk_storage" {
  description = "Primary datastore for future VM and container disks."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_vm_disk_storage)) > 0
    error_message = "proxmox_vm_disk_storage must be a non-empty string."
  }
}

variable "proxmox_iso_storage" {
  description = "Datastore used for ISOs."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_iso_storage)) > 0
    error_message = "proxmox_iso_storage must be a non-empty string."
  }
}

variable "proxmox_snippet_storage" {
  description = "Datastore used for snippets and cloud-init fragments."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_snippet_storage)) > 0
    error_message = "proxmox_snippet_storage must be a non-empty string."
  }
}

variable "proxmox_template_storage" {
  description = "Datastore used for templates or container images."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_template_storage)) > 0
    error_message = "proxmox_template_storage must be a non-empty string."
  }
}

variable "proxmox_bridge_name" {
  description = "Default bridge for future guests."
  type        = string

  validation {
    condition     = length(trimspace(var.proxmox_bridge_name)) > 0
    error_message = "proxmox_bridge_name must be a non-empty string."
  }
}

variable "proxmox_management_cidr" {
  description = "Management network CIDR."
  type        = string

  validation {
    condition     = can(cidrhost(var.proxmox_management_cidr, 0))
    error_message = "proxmox_management_cidr must be a valid CIDR."
  }
}

variable "proxmox_management_gateway" {
  description = "Management network gateway."
  type        = string

  validation {
    condition     = can(cidrhost("${var.proxmox_management_gateway}/32", 0))
    error_message = "proxmox_management_gateway must be a valid IPv4 address."
  }
}

variable "proxmox_management_domain" {
  description = "DNS domain assigned to guests during initialization."
  type        = string
}

variable "proxmox_management_dns_servers" {
  description = "DNS servers assigned to guests during initialization."
  type        = list(string)

  validation {
    condition = alltrue([
      for server in var.proxmox_management_dns_servers :
      can(cidrhost("${server}/32", 0))
    ])
    error_message = "proxmox_management_dns_servers must contain only valid IPv4 addresses."
  }
}

variable "proxmox_hosts" {
  description = "Host matrix generated from config/home.yaml."
  type = map(object({
    node_name            = string
    management_address   = string
    management_cidr      = string
    tailscale_hostname   = string
    management_interface = string
    inventory_groups     = list(string)
  }))
}

variable "proxmox_api_token" {
  description = "Runtime-injected Proxmox API token."
  type        = string
  sensitive   = true
}

variable "cluster_operator_user" {
  description = "Cloud-init username for the homelab-core guests."
  type        = string
}

variable "cluster_operator_ssh_public_key" {
  description = "SSH public key injected into homelab-core guests via cloud-init."
  type        = string
  sensitive   = true
}

variable "cluster_template" {
  description = "Template VM definition for the homelab-core guests."
  type = object({
    vm_id           = number
    name            = string
    image_url       = string
    image_file_name = string
    disk_gb         = number
  })
}

variable "cluster_nodes" {
  description = "homelab-core VM definitions."
  type = map(object({
    vm_id              = number
    role               = string
    management_address = string
    management_cidr    = string
    cpu_cores          = number
    memory_mb          = number
    disk_gb            = number
    inventory_groups   = list(string)
  }))
}

variable "home_assistant" {
  description = "Home Assistant VM definition."
  type = object({
    name               = string
    vm_id              = number
    management_address = string
    management_cidr    = string
    mac_address        = string
    cpu_cores          = number
    memory_mb          = number
    disk_gb            = number
    datastore_id       = string
    start_on_boot      = bool
    tags               = list(string)
    description        = string
  })
}

variable "openclaw_gateways" {
  description = "OpenClaw gateway VM definitions."
  type = map(object({
    vm_id              = number
    bot_slug           = string
    management_address = string
    mac_address        = string
    cpu_cores          = number
    memory_mb          = number
    disk_gb            = number
    start_on_boot      = bool
    install_tailscale  = bool
    inventory_groups   = list(string)
  }))
  default = {}
}

variable "containers" {
  description = "LXC container definitions."
  type = map(object({
    ct_id              = number
    role               = string
    management_address = string
    management_cidr    = string
    template_url       = string
    template_file_name = string
    cpu_cores          = number
    memory_mb          = number
    swap_mb            = number
    disk_gb            = number
    unprivileged       = bool
    nesting            = bool
    start_on_boot      = bool
  }))
  default = {}
}

variable "proxmox_ssh_username" {
  description = "Runtime-injected SSH username used by the provider when SSH access is required."
  type        = string
  sensitive   = true
}

variable "proxmox_ssh_private_key" {
  description = "Runtime-injected SSH private key used by the provider when SSH access is required."
  type        = string
  sensitive   = true
}

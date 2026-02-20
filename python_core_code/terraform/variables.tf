variable "os_token" {
  type        = string
  sensitive   = true
  description = "OpenStack scoped token"
}

variable "auth_url" {
  type        = string
  description = "mmmm"
}

variable "laniakea_description" {
  type        = string
  default     = " "
  description = "User-defined description for the Laniakea deployment"
}

variable "os_tenant_id" {
  type        = string
  description = "OpenStack tenant/project ID"
}

variable "region" {
  type    = string
  default = "RegionOne"
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key content"
}

variable "bastion_ip" {
  type        = string
  description = "CIDR or IP allowed to SSH (e.g. 10.0.0.10/32)"
}

variable "image_name" {
  type    = string
  default = "Ubuntu 22.04"
}

variable "flavor_name" {
  type    = string
  default = "m1.small"
}


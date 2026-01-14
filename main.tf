terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "azurerm" {
  features {}
}

# RANDOM SUFFIX (na storage jeśli potrzebny)
resource "random_string" "random" {
  length  = 6
  upper   = false
  special = false
}

# RESOURCE GROUP
resource "azurerm_resource_group" "rg" {
  name     = "iad-lab-rg-projekt"
  location = "Poland Central"
}

# STORAGE ACCOUNT (ADLS Gen2)
resource "azurerm_storage_account" "storage" {
  name                     = "iadoutputstoragensprojekt"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location

  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true   # ADLS Gen2
}

# EVENT HUB NAMESPACE
resource "azurerm_eventhub_namespace" "eh_ns" {
  name                = "event-hubs-ns-ns-projekt"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  sku                 = "Basic"   # najtańsza opcja
  capacity            = 1
}

# EVENT HUB
resource "azurerm_eventhub" "eh" {
  name                = "input-stream-projekt"
  namespace_name      = azurerm_eventhub_namespace.eh_ns.name
  resource_group_name = azurerm_resource_group.rg.name

  partition_count     = 2
  message_retention   = 1
}

# OUTPUTS
output "eventhub_namespace" {
  value = azurerm_eventhub_namespace.eh_ns.name
}

output "eventhub_name" {
  value = azurerm_eventhub.eh.name
}

output "storage_account_name" {
  value = azurerm_storage_account.storage.name
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

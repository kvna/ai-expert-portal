terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "this" {
  name     = "rg-ai-expert-portal"
  location = "westeurope" # Static Web Apps is only available in a handful of regions; this is the nearest one that supports it.
}

# Free tier: $0 at rest, no compute runs for a page view -- the site is a
# pre-rendered static build (see ../ai-expert-portal/build_static.py),
# deployed by a GitHub Actions workflow on every push to master.
resource "azurerm_static_web_app" "this" {
  name                = "ai-expert-portal"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku_tier            = "Free"
  sku_size            = "Free"
}

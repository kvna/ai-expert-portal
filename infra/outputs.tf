output "default_hostname" {
  description = "The public URL the portal will be served from."
  value       = "https://${azurerm_static_web_app.this.default_host_name}"
}

output "deployment_token" {
  description = "Deployment token for the GitHub Actions workflow. Set as the AZURE_STATIC_WEB_APPS_API_TOKEN repo secret -- never commit it."
  value       = azurerm_static_web_app.this.api_key
  sensitive   = true
}

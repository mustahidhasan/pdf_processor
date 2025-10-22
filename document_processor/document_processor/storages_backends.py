from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
    account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
    azure_container = settings.AZURE_BLOB_CONTAINER_NAME
    expiration_secs = None  # URLs won't expire

    def _save(self, name, content):
        saved_name = super()._save(name, content)
        print(f"✅ File saved to Azure Blob Storage: {saved_name}")
        return saved_name

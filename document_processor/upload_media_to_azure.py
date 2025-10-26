import os
from azure.storage.blob import BlobServiceClient

# Azure Storage config
AZURE_STORAGE_ACCOUNT_NAME = "splitterstorage"
AZURE_STORAGE_ACCOUNT_KEY = "UiI3HzkXvAud0u/JzCn+CsLa24zNfcyM9xlqAvt7X2bhM1aa6OpVBXxgtc4qgRvbznnlBloLpM+J+ASt3LxSOA=="
AZURE_BLOB_CONTAINER_NAME = "comax-images-db"

# Build connection string
AZ_CONN = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={AZURE_STORAGE_ACCOUNT_NAME};"
    f"AccountKey={AZURE_STORAGE_ACCOUNT_KEY};"
    f"EndpointSuffix=core.windows.net"
)

# Local media folder
MEDIA_ROOT = "/home/mustahid/Work/Personal/pdf_processor/document_processor/media"

# Initialize BlobServiceClient
client = BlobServiceClient.from_connection_string(AZ_CONN)
container = client.get_container_client(AZURE_BLOB_CONTAINER_NAME)

# Walk through all files in MEDIA_ROOT and upload
for root, dirs, files in os.walk(MEDIA_ROOT):
    for file in files:
        local_path = os.path.join(root, file)
        # Compute blob path relative to MEDIA_ROOT
        blob_path = os.path.relpath(local_path, MEDIA_ROOT).replace(os.path.sep, "/")
        print(f"Uploading {blob_path} ...")
        with open(local_path, "rb") as data:
            container.upload_blob(name=blob_path, data=data, overwrite=True)

print("✅ All media files uploaded successfully!")

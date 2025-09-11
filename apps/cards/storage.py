from storages.backends.s3 import S3Storage
from django.conf import settings

class MediaStorage(S3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    file_overwrite = False
    default_acl = None  # 不使用 ACL

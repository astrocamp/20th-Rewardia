from storages.backends.s3 import S3Storage
from django.conf import settings

class MediaStorage(S3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    location = 'media'  # 這樣 key 和 URL 都會帶 media/
    file_overwrite = False
    default_acl = None  # 不使用 ACL
    
    def url(self, name):
        """生成正確的 S3 URL"""
        # 直接使用父類的 url 方法，讓 storages 自動處理 location
        return super().url(name)

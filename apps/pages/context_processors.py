import os
from datetime import datetime


def get_build_version():
    # 優先使用環境變數中的建構時間
    build_time = os.environ.get("BUILD_TIME")
    if build_time:
        return build_time

    # 如果沒有環境變數，返回當前時間
    return datetime.now().strftime("%Y%m%d%H%M")


STATIC_VERSION_HASH = get_build_version()

def version(request):
    return {"STATIC_VERSION": STATIC_VERSION_HASH}

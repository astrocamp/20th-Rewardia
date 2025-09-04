from celery import shared_task
from django.core.management import call_command
from io import StringIO


@shared_task
def crawl_roo_task():
    from celery.utils.log import get_task_logger

    logger = get_task_logger(__name__)
    with StringIO() as output:
        try:
            call_command("crawl_roo", stdout=output, stderr=output)

            result = output.getvalue()
            logger.info("爬蟲任務成功完成。")
            return {"status": "success", "message": "爬蟲完成", "output": result}

        except Exception as e:
            logger.error(f"爬蟲任務失敗: {e}\n輸出:\n{output.getvalue()}")
            raise

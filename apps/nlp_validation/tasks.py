from celery import shared_task
from django.core.management import call_command
from io import StringIO


@shared_task
def run_nlp_validation_task():
    from celery.utils.log import get_task_logger

    logger = get_task_logger(__name__)
    with StringIO() as output:
        try:
            call_command("run_nlp_validation", stdout=output, stderr=output)

            result = output.getvalue()
            logger.info("NLP 分析任務成功完成。")
            return {"status": "success", "message": "NLP分析完成", "output": result}

        except Exception as e:
            logger.error(f"NLP 分析任務失敗: {e}\n輸出:\n{output.getvalue()}")
            raise

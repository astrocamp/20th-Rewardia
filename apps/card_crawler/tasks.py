from celery import shared_task
from django.core.management import call_command
from io import StringIO


@shared_task
def crawl_roo_task():
    output = StringIO()

    try:
        call_command("crawl_roo", stdout=output, stderr=output)

        result = output.getvalue()
        return {"status": "success", "message": "爬蟲完成", "output": result}

    except Exception as e:
        return {
            "status": "error",
            "message": f"爬蟲失敗: {str(e)}",
            "output": output.getvalue(),
        }

    finally:
        output.close()

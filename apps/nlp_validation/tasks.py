from celery import shared_task
from django.core.management import call_command
from io import StringIO


@shared_task
def run_nlp_validation_task():
    output = StringIO()

    try:
        call_command("run_nlp_validation", stdout=output, stderr=output)

        result = output.getvalue()
        return {"status": "success", "message": "NLP分析完成", "output": result}

    except Exception as e:
        return {
            "status": "error",
            "message": f"NLP分析失敗: {str(e)}",
            "output": output.getvalue(),
        }

    finally:
        output.close()

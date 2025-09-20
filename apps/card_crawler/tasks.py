from celery import shared_task
from django.core.management import call_command
from io import StringIO
from celery.utils.log import get_task_logger


@shared_task
def crawl_roo_task():
    logger = get_task_logger(__name__)
    with StringIO() as output:
        crawl_success = False
        nlp_success = False
        
        # 爬蟲階段
        try:
            call_command("crawl_roo", stdout=output, stderr=output)
            logger.info("爬蟲任務成功完成。")
            crawl_success = True
        except Exception as e:
            logger.error(f"爬蟲失敗: {e}")
            # 不要 raise，繼續執行 NLP
        
        # NLP階段（不管爬蟲成功與否都執行）
        try:
            logger.info("開始 NLP 分析...")
            call_command("run_nlp_validation", stdout=output, stderr=output)
            logger.info("NLP 分析完成。")
            nlp_success = True
        except Exception as e:
            logger.error(f"NLP分析失敗: {e}")
        
        # 決定最終狀態
        if crawl_success and nlp_success:
            status = "success"
            message = "爬蟲和NLP分析全部完成"
        elif crawl_success:
            status = "partial_success"
            message = "爬蟲完成，NLP分析失敗"
        elif nlp_success:
            status = "partial_success"  
            message = "爬蟲失敗，NLP分析完成"
        else:
            status = "failed"
            message = "爬蟲和NLP分析都失敗"
        
        result = output.getvalue()
        return {"status": status, "message": message, "output": result}

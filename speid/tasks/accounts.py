from speid.tasks import celery


@celery.task(bind=True, max_retries=None)
def create_account(self, account):
    raise NotImplementedError

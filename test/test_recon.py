import os

import boto3
import pytest

from speid import db
from speid.models import Transaction
from speid.recon import reconciliate


@pytest.mark.vcr()
def test_reconciliate(file_recon):
    s3 = boto3.resource(
        's3',
        region_name='us-east-1',
        aws_access_key_id=os.environ['RECON_AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['RECON_AWS_SECRET_ACCESS_KEY'],
    )
    s3.meta.client.put_object(
        Body=file_recon, Bucket=os.environ['RECON_BUCKET_S3'], Key='reports/report.txt'
    )
    reconciliate()
    transaction = (
        db.session.query(Transaction).filter_by(orden_id=22673742).first()
    )
    assert transaction

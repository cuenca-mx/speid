import os

import boto3

from speid import db
from speid.models import Transaction
from speid.recon import reconciliate
from test.custom_vcr import my_vcr


@my_vcr.use_cassette('test/cassettes/test_recon.yaml')
def test_reconciliate(file_recon):
    s3 = boto3.resource(
        's3',
        region_name='us-east-1',
        aws_access_key_id=os.environ['RECON_AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['RECON_AWS_SECRET_ACCESS_KEY'],
    )
    s3.meta.client.put_object(
        Body=file_recon,
        Bucket=os.environ['RECON_BUCKET_S3'],
        Key='reports/report.txt',
    )
    reconciliate()
    transaction = (
        db.session.query(Transaction).filter_by(orden_id=22673742).first()
    )
    assert transaction

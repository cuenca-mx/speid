import logging
from test.custom_vcr import my_vcr
import pytest

from speid import db
from speid.models import Transaction
from speid.recon import recon_transactions
from speid.tables.types import Estado


logging.basicConfig()

vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.DEBUG)


class TestRecon:
    @my_vcr.use_cassette('test/cassettes/test_recon.yaml')
    def test_reconciliate_status_failed(self, file_recon):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon)
        recon_transactions()
        transaction = (
            db.session.query(Transaction).filter_by(
                orden_id=22673742
            ).first()
        )
        assert transaction.estado == Estado.failed

    @my_vcr.use_cassette('test/cassettes/test_recon1.yaml')
    def test_reconciliate_succeeded(self, file_recon1):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon1)
        recon_transactions()
        transaction = (
            db.session.query(Transaction).filter_by(
                orden_id=22672732,
                clave_rastreo='HG745321'
            ).first()
        )
        assert transaction

    @my_vcr.use_cassette('test/cassettes/test_recon2.yaml')
    def test_reconciliate_wrong_account(self, file_recon2):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon2)
        recon_transactions()
        transaction = (
            db.session.query(Transaction).filter_by(
                orden_id=22673745,
                clave_rastreo='GH458434'
            ).first()
        )
        assert transaction

    def test_reconciliate_exception(self, file_recon3):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon3)
        with pytest.raises(KeyError):
            recon_transactions()

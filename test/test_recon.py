import logging
from test.custom_vcr import my_vcr

from speid import db
from speid.models import Transaction
from speid.recon import recon_transactions


logging.basicConfig()

vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.DEBUG)


class TestRecon:
    @my_vcr.use_cassette('test/cassettes/test_recon.yaml')
    def test_reconciliate(self, file_recon):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon)
        recon_transactions()
        transaction = (
            db.session.query(Transaction).filter_by(
                orden_id=22673742,
                clave_rastreo='CR1547453521',
                estado='failed'
            ).first()
        )
        assert transaction

        transaction = (
            db.session.query(Transaction).filter_by(
                orden_id=22672732,
                clave_rastreo='HG745321'
            ).first()
        )
        assert transaction

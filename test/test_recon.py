from test.custom_vcr import my_vcr

from speid import db
from speid.models import Transaction
from speid.recon import recon_transactions


class TestRecon:
    @my_vcr.use_cassette('test/cassettes/test_recon.yaml')
    def test_reconciliate(self, file_recon):
        with open('/tmp/report.txt', 'w') as f:
            f.write(file_recon)
        recon_transactions()
        # transaction = (
        #     db.session.query(Transaction).filter_by(orden_id=22673742).first()
        # )
        # assert transaction
        transaction = (
            db.session.query(Transaction)
        )
        assert transaction.all() == 'testing'

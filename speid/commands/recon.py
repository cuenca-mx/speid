from speid.recon import reconciliate as r
from speid import app


@app.cli.group('recon')
def recon_group():
    """Perform recon actions."""
    pass


@recon_group.command('reconciliate')
def reconciliate():
    r()

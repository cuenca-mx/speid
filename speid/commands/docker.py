import docker

from speid import app, db

DB_CONTAINER_NAME = 'speid_db'


@app.cli.group('docker')
def docker_group():
    """Perform docker actions."""
    pass


@docker_group.command()
def create_db():
    client = docker.from_env()
    ports = {'27017/tcp': db.engine.url.port}
    client.containers.run(
        'mongo:4.0',
        detach=True,
        auto_remove=True,
        name=DB_CONTAINER_NAME,
        ports=ports,
    )


@docker_group.command()
def drop_db():
    client = docker.from_env()
    filters = dict(name=DB_CONTAINER_NAME)
    db_container = client.containers.list(filters=filters)[0]
    db_container.stop()

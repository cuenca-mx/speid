import datetime as dt
import json
import os
from dataclasses import dataclass
from enum import Enum
from unittest.mock import MagicMock, patch

import boto3
from moto import mock_s3

from speid import CJSONEncoder, configure_environment

DOWNLOAD_PATH = os.environ['STP_PRIVATE_LOCATION']
KEY_NAME = os.environ['STP_PRIVATE_KEY']
STP_BUCKET_S3 = os.environ['STP_BUCKET_S3']


@mock_s3
def test_download_key_from_s3():
    client = boto3.client('s3', region_name='us-east-1')
    client.create_bucket(Bucket=STP_BUCKET_S3)
    client.upload_file(DOWNLOAD_PATH, STP_BUCKET_S3, KEY_NAME)

    with open(DOWNLOAD_PATH) as file:
        file_content = file.read()

    with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'testing'}):
        configure_environment()

        with open(DOWNLOAD_PATH) as file:
            assert file_content == file.read()


@patch('speid.Hosts.add')
@patch('speid.Hosts.write', return_value=None)
def test_edit_hosts(_, mock_hosts_add: MagicMock):
    with patch.dict(
        os.environ,
        {'EDIT_HOSTS': 'true', 'HOST_IP': '1.0.0.1', 'HOST_AD': 'test.com'},
    ):
        configure_environment()
        args = mock_hosts_add.call_args[0]
        host_entry = args[0][0]
        assert host_entry.entry_type == 'ipv4'
        assert host_entry.address == '1.0.0.1'
        assert host_entry.names == ['test.com']


def test_json_encoder():
    class EnumTest(Enum):
        s, p, e, i, d = range(5)

    @dataclass
    class TestClass:
        uno: str

        def to_dict(self):
            return dict(uno=self.uno, dos='dos')

    now = dt.datetime.utcnow()
    test_class = TestClass(uno='uno')

    to_encode = dict(enum=EnumTest.s, now=now, test_class=test_class)

    encoded = json.dumps(to_encode, cls=CJSONEncoder)
    decoded = json.loads(encoded)

    assert decoded['enum'] == 's'
    assert decoded['now'] == now.isoformat() + 'Z'
    assert decoded['test_class']['uno'] == 'uno'
    assert decoded['test_class']['dos'] == 'dos'

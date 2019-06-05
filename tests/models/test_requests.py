from speid.models import Request
from speid.types import HttpRequestMethod


def test_requests():
    request = Request(
        method=HttpRequestMethod.post,
        path='/path',
        query_string='x=1',
        ip_address='127.0.0.1',
        headers={"auth": "test", "Content-Type": "json"},
        body='The body',
    )
    request.save()
    query_request = Request.objects.get(id=request.id)
    assert query_request.method == request.method
    assert query_request.path == request.path
    assert query_request.query_string == request.query_string
    assert query_request.ip_address == request.ip_address
    assert query_request.headers == request.headers
    assert query_request.body == request.body
    request.delete()

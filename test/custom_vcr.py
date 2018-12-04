import vcr


def set_orden_id(request):
    if 'set/' in request.uri:
        request.uri = 'https://testapi/set/5694433'
    return request


my_vcr = vcr.VCR(
    before_record_request=set_orden_id,
    ignore_hosts={'sentry.io', '127.0.0.1'},
    ignore_localhost=True
)

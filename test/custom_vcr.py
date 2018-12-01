import vcr
import random


random_list = [1234567, 1234566, 1234569, 1234568]


def set_orden_id(request):
    if 'set/' in request.uri:
        request.uri = 'https://testapi/set/5694433'
    return request


def set_orden_random_id(response):

    if '<id>5554988</id>' in str(response['body']['string']):
        random_int = str(random_list(random.randint(1, 4)))
        body_content = str(response['body']['string'])\
            .replace('5554988', random_int)
        print(body_content)
        response['body']['string'] = body_content
    return response


my_vcr = vcr.VCR(
    before_record_request=set_orden_id,
    ignore_hosts={'sentry.io', 'stpmex.com', '127.0.0.1'},
    ignore_localhost=True
)

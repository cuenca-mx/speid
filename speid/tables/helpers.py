import uuid


def base62_encode(num):
    # http://stackoverflow.com/questions/1119722/base-62-conversion

    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        num, rem = divmod(num, base)
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base62_uuid(prefix=''):
    def base62_uuid_func():
        return prefix + base62_encode(uuid.uuid1().int)
    return base62_uuid_func

import base64
import binascii
import hashlib


def measure(value):
    if not isinstance(value, str) or len(value) > 175_000:
        raise ValueError('副本载荷过大或缺失')
    try:
        contents = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError('副本编码无效') from error
    return str(len(contents)), hashlib.sha256(contents).hexdigest()

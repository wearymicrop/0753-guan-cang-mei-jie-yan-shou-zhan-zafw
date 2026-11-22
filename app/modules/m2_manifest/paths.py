import re
import unicodedata


def normalize(value):
    if not isinstance(value, str) or not value or len(value) > 500:
        raise ValueError('相对路径不能为空')
    text = unicodedata.normalize('NFC', value.replace('\\', '/'))
    if text.startswith('/') or ':' in text or any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError('拒收绝对路径或控制字符')
    parts = []
    for part in text.split('/'):
        if part == '..':
            raise ValueError('拒收上级路径')
        if part and part != '.':
            parts.append(part)
    if not parts or text.endswith('/'):
        raise ValueError('路径需指向条目')
    return '/'.join(parts)


def checksum(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-fA-F0-9]{64}', value):
        raise ValueError('SHA-256 无效')
    return value.lower()

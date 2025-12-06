def is_empty_string(s):
    """
    判断字符串是否为None、空字符串或全是空格
    """
    if s is None or s.strip() == "":
        return True
    return False

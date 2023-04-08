from utils.constants import TAG_SPLITTER


def str_to_tag(tag_str) -> list:
    tag_list = ['', '']
    if TAG_SPLITTER in tag_str:
        tag_list = tag_str.split(TAG_SPLITTER)
    else:
        tag_list[1] = tag_str
    return tag_list


def tag_to_str(tag) -> str:
    if tag[0]:
        group = tag[0] + TAG_SPLITTER
    else:
        group = ''
    return group + tag[1]

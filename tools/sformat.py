
words = """  """

def cssformat(words):
    nwords = r""
    for c in words:
        if c=='{':
            nwords = nwords + c + "\n" + "    "
        elif c=='}':
            nwords = nwords + "\n" + c + "\n"
        else:
            nwords = nwords + c
    print(nwords)



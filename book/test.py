


def mydeco(f):
    # This function is what we "replace" hello with
    def wrapper(*args, **kw):
        print(args[0])
        print(args[1])
        return f(*args, **kw)  # Call hello

    return wrapper



@mydeco
def person(name,age,address,code):
    print(name,age,address,code)

person("test",12,333,444)
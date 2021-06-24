import re

def atom_clause_covert(sent_list:list, verb:str, atom:str):
    r1 = re.compile(r"(.+)\((.+)\)")
    r2 = re.compile(r"(ARG[0-9]+)\:(.+)")
    r3 = re.compile(r"(ARG[0-9]+)=(.+)")
    lst = r1.match(atom).groups()[1].split(",")
    for index, item in enumerate(lst):
        lst[index] = item.replace(" ","")
    dis = dict()
    for item in lst:
        res = r3.match(item).groups()
        dis[res[0]] = res[1]

    for i,val in enumerate(sent_list):
        if val == "V":
            sent_list[i] = verb
        if "ARG" in val:
            res = r2.match(val).groups()
            if res[1] != "PER":
                sent_list[i] = res[1]
            else:
                sent_list[i] = dis[res[0]]


    return " ".join(sent_list)


print(atom_clause_covert(["ARG0:PER","V","ARG1:PER","ARG2:of stealing"],"accuse","accuse_of_stealing(ARG0=x, ARG1=y)"))

def process(s):
    return s

def string_transer(data:str):
    and_ = None
    if "and" in data:
        and_ = True
        lst = data.split("and")
    elif "or" in data:
        and_ = False
        lst = data.split("or")
    else:
        return process(data)
    for i,val in enumerate(lst):
        lst[i] = process(val)
    if and_:
        return " ^ ".join(lst)
    else:
        return " v ".join(lst)

def function_transfer(data:str):
    r1 = re.compile(r"(.+)\((.+)\)")
    r2 = re.compile(r"ARG[0-9]+=(.+)")
    data = r1.match(data).groups()
    lst1 = data[1].split(",")
    print(lst1)
    lst2 = []
    for item in lst1:
        st = r2.search(item).groups()[0]
        lst2.append(st)
    print(lst2)
    return data[0]+"("+", ".join(lst2)+")"

print(function_transfer("accuse_of_stealing(ARG0=x, ARG1=y)"))


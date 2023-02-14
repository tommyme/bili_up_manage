import pickle
import pandas as pd
import sanic

def filter(obj, useful_keys):
    return {i:obj[i] for i in obj if i in useful_keys}

def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def dump_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def dict2dict(origin, key_dict):
    return {key_dict[i]:origin[i] for i in origin}

def copyColInTable(table: pd.DataFrame, data:dict):
    for _from, _to in data.items():
        table.loc[:, _to] = table[_from]

def table2dict(table: pd.DataFrame):
    return table.to_dict(orient='records')

def param_or_fail(*params):
    def deco(f):
        def wrapper(request: sanic.Request):
            for param in params:
                if request.args.get(param) is None:
                    return sanic.response.text("param error")
            return f(request)
        return wrapper
    return deco

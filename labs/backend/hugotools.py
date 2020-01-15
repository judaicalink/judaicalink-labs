import toml
import json
import yaml

def get_toml(file, encoding="utf-8"):
    in_toml = False
    toml_string = ""
    with open(file, "r", encoding=encoding) as f:
        for line in f:
            if line.strip()=="+++":
                if not in_toml:
                    in_toml = True
                    continue
                else:
                    return toml.loads(toml_string)
            if in_toml:
                toml_string = "\n".join((toml_string, line))

def get_yaml(file, encoding="utf-8"):
    in_yaml = False
    yaml_string = ""
    with open(file, "r", encoding=encoding) as f:
        for line in f:
            if line.strip()=="---":
                if not in_yaml:
                    in_yaml = True
                    continue
                else:
                    return yaml.load(yaml_string)
            if in_yaml:
                yaml_string = "\n".join((yaml_string, line))

def get_json(file, encoding="utf-8"):
    in_json = False
    json_string = ""
    with open(file, "r", encoding=encoding) as f:
        for line in f:
            if line[0]=="{":
                if not in_json:
                    in_json = True
            if in_json:
                json_string = "\n".join((json_string, line))
            if line[0]=="}":
                return json.loads(json_string)

def get_data(file, encoding="utf-8"):
    line = ""
    with open(file, "r", encoding=encoding) as f:
        line = f.readline().strip()
    if line=="---":
        return get_yaml(file, encoding)
    elif line=="+++":
        return get_toml(file, encoding)
    elif line=="{":
        return get_json(file, encoding)
    else:
        return dict()

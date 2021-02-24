import yaml


def load_yaml(file_path):
    """
    Loads a yaml file

    Parameters
    ----------
    file_path : Path
        File path

    Returns
    -------
    Object
        Yaml object
    """
    with open(file_path) as f:
        data = f.read()
    return yaml.load(data, Loader=yaml.FullLoader)


def dump_yaml(file_path, yaml_doc):
    """
    Writes a yaml object to a file

    Parameters
    ----------
    file_path : Path
        File path
    yaml_doc : Object
        Yaml object
    """
    with open(file_path, "w") as f:
        yaml.dump(yaml_doc, f)

from json import dump as dump_js, load as load_js
from pickle import load as load_pkl, dump as dump_pkl, HIGHEST_PROTOCOL
from os import mkdir
from os.path import join, exists
from sys import exc_info
from typing import Union


def read_file(file_name: str, path: str, file_format: str) -> Union[dict, None]:
    try:
        if file_format == "json":
            full_path = join(path, "%s.json" % file_name)
            with open(full_path, "r") as outfile:
                data = load_js(outfile)
        elif file_format == "pickle":
            full_path = join(path, "%s.pkl" % file_name)
            with open(full_path, "rb") as outfile:
                data = load_pkl(outfile)
        else:
            print(
                "ERROR, '%s': file_format must be either 'json' or 'pickle', '%s' was given."
                % (read_file.__name__, file_format)
            )
            raise Exception(
                "file_format must be either 'json' or 'pickle', '%s' was given."
                % file_format
            )

    except OSError as err:
        print(
            "ERROR, '%s': Could not load data from '%s'. (%s, OSError: %i)"
            % (read_file.__name__, full_path, err.strerror, err.errno)
        )
        return None
    except:
        print(
            "DEBUG, '%s': %s: '%s'."
            % (read_file.__name__, exc_info()[0].__name__, exc_info()[1])
        )
        raise

    else:
        pass
        # print("INFO, '%s': Loaded data from '%s'." % (read_file.__name__, full_path))

    return data


def write_file(data: dict, file_name: str, path: str, file_format: str) -> None:

    try:
        if not exists(path):
            mkdir(path)

    except OSError as err:
        print(
            "ERROR, '%s': Could not create '%s' or check its existence. (%s, OSError: %i)"
            % (write_file.__name__, path, err.strerror, err.errno)
        )
        return None
    except:
        print(
            "DEBUG, '%s': %s: '%s'."
            % (read_file.__name__, exc_info()[0].__name__, exc_info()[1])
        )
        raise

    try:
        if file_format == "json":
            full_path = join(path, "%s.json" % file_name)
            with open(full_path, "w") as outfile:
                dump_js(data, outfile, indent=4)
        elif file_format == "pickle":
            full_path = join(path, "%s.pkl" % file_name)
            with open(full_path, "wb") as outfile:
                dump_pkl(data, outfile, protocol=HIGHEST_PROTOCOL)
        else:
            print(
                "ERROR, '%s': file_format must be either 'json' or 'pickle', '%s' was given."
                % (write_file.__name__, file_format)
            )
            raise Exception(
                "file_format must be either 'json' or 'pickle', '%s' was given."
                % file_format
            )

    except OSError as err:
        print(
            "ERROR, '%s': Could not write data to '%s'. (%s, OSError: %i)"
            % (write_file.__name__, full_path, err.strerror, err.errno)
        )
    except:
        print(
            "DEBUG, '%s': %s: '%s'."
            % (read_file.__name__, exc_info()[0].__name__, exc_info()[1])
        )
        raise
    else:
        pass
        # print("INFO, '%s': Wrote data to '%s'." % (write_file.__name__, full_path))

    return None


if __name__ == "__main__":

    # make those unit tests
    pass

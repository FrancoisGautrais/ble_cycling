from pathlib import Path

def read_csv_elite(path):
    headers = []
    data = []
    with open(path) as fd:
        for i, line in enumerate(fd.readlines()):
            if not i:
                headers = line.replace(" ", "").lower().split(",")
            else:
                ld = dict(zip(headers,
                              [(float(x) if "." in x else int(x)) for x in line.replace(" ", "").split(",")]
                ))
                ld["time"] /= 1000
                data.append(ld)
    return data


import random

def create_file(filename: str) -> str:
    with open(filename, 'w') as file:
        file.write("[\n")
        for i in range(100):
            file.write("[")
            for j in range(80):
                file.write(str(random.random()) + ",") if j != 79 else file.write(str(random.random()))
            file.write("]") if i == 99 else file.write("],")
            file.write("\n")

        file.write("]")


create_file('med_mem_multi_run.json')
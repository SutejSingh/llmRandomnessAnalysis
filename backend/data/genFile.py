import random
n = 100
r = 10

def create_file(filename: str) -> str:
    with open(filename, 'w') as file:
        file.write("[\n")
        for i in range(r):
            file.write("[")
            for j in range(n):
                file.write(str(random.random()) + ",") if j != n-1 else file.write(str(random.random()))
            file.write("]") if i == r-1 else file.write("],")
            file.write("\n")

        file.write("]")


create_file('normal_run.json')
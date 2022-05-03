import concurrent.futures
import time
import random

def some_func(n, k):
    st = time.time()
    l = [[j*i for j in range(3000)] for i in range(1000)]
    for i in range(len(l)):
        for j in range(len(l[i])):
            l[i][j] *= n

    return f'func №_{k} work {time.time()-st} sec'


if __name__ == "__main__":
    x = 17
    st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor: #Оптимальное кол-во вызванных процессов 3-4
        future_to_item = [executor.submit(some_func, 999, n) for n in range(1, x)]
        for future in concurrent.futures.as_completed(future_to_item):
            print(future.result())
    print(f'___Processes working {time.time()-st} sec')

    st1 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_item = [executor.submit(some_func, 999, n) for n in range(1, x)]
        for future in concurrent.futures.as_completed(future_to_item):
            print(future.result())
    print(f'___Treads working {time.time()-st1} sec')

    st2 = time.time()
    for i in range(1, x):
        print(some_func(999, i))
    print(f'___Funcs working {time.time()-st2} sec')
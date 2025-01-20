import multiprocessing
import json
import threading
import os
import random
import time

stop_event = threading.Event()

def calculate_element(args):
    i, j, matrix1, matrix2 = args
    result = 0
    N = len(matrix1[0])
    for k in range(N):
        result += matrix1[i][k] * matrix2[k][j]
    with open('intermediate_results.txt', 'a') as f:
        f.write(f"Element ({i}, {j}): {result}\n")
    return result

def perform_elementwise_multiplication(matrix1, matrix2, num_processes=4):
    if len(matrix1) != len(matrix2[0]):
        raise ValueError("Матрицы должны иметь одинаковые размеры!")
    rows = len(matrix1)
    cols = len(matrix2[0])
    args = [(i, j, matrix1, matrix2) for i in range(rows) for j in range(cols)]

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(calculate_element, args)

    results = [res for res in results if res is not None]  # Удаление результатов, если произошла остановка
    if len(results) != rows * cols:
        return None

    result_matrix = [results[i:i + cols] for i in range(0, len(results), cols)]
    return result_matrix


def generate_random_matrix(size):
    return [[random.random() for _ in range(size)] for _ in range(size)]

def save_matrix_to_file(matrix, filename):
    with open(filename, 'a') as f:
        json.dump(matrix, f)


def load_matrix_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_matrix_to_file(matrix, filename):
    with open(filename, 'w') as f:
        json.dump(matrix, f)

def matrix_multiplication_from_file():
    try:
        matrix1 = load_matrix_from_file('matrix1.json')
        matrix2 = load_matrix_from_file('matrix2.json')

        open('intermediate_results.txt', 'w').close()  # Очистка промежуточного файла

        result_matrix = perform_elementwise_multiplication(matrix1, matrix2)
        save_matrix_to_file(result_matrix, 'result.txt')
        print("Результат сохранен в result.txt и intermediate_results.txt")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при чтении файлов: {e}")
    except ValueError as e:
        print(f"Ошибка: {e}")

def matrix_multiplication_worker(matrix_size, num_processes, queue):
    while not stop_event.is_set():
        matrix1 = generate_random_matrix(matrix_size)
        matrix2 = generate_random_matrix(matrix_size)
        try:
            result_matrix = perform_elementwise_multiplication(matrix1, matrix2, num_processes)
            if result_matrix is not None:
                queue.put((matrix1, matrix2, result_matrix))
        except ValueError as e:
            print(f"Ошибка: {e}")
        time.sleep(0.1)


if __name__ == '__main__':
    print('Сначала выполняется умножение матриц из файлов:')
    matrix_multiplication_from_file()

    matrix_size = int(input("Введите размерность квадратных матриц: "))
    num_processes = os.cpu_count()

    queue = multiprocessing.Queue()
    worker_thread = multiprocessing.Process(target=matrix_multiplication_worker, args=(matrix_size, num_processes, queue))
    worker_thread.start()

    try:
        while True:
            command = input("Введите 0 для остановки, или что-нибудь еще для продолжения: ")
            if command.lower() == '0':
                stop_event.set()
                worker_thread.join()
                break
            time.sleep(1)
            while not queue.empty():
                matrix1, matrix2, result_matrix = queue.get()
                save_matrix_to_file(result_matrix, 'result_all.txt') # перезапись в один файл
                print("Результат перемножения сохранен в result_all.txt")
    except KeyboardInterrupt:
        stop_event.set()
        worker_thread.join()
        print("Процесс остановлен.")
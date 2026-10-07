import sys


def fib(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    previous = 0
    current = 1
    index = 1
    while index < n:
        next_value = previous + current
        previous = current
        current = next_value
        index = index + 1
    return current


def main():
    n = int(sys.argv[1])
    result = fib(n)
    print(result)


if __name__ == "__main__":
    main()

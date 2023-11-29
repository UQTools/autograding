def identity(x):
    return x

def doubler():
    x = int(input())
    print(x * 2)

def greeter():
    first_name = input()
    last_name = input()

    print(f'Hello {first_name} {last_name}')

def museum():
    print("Welcome to the Museum")
    print("Say thank you? (y/n)")
    answer = input()
    if answer == "y":
        print("You're welcome!")
    else:
        return

    print("What's your name?")
    name = input()
    print(f"Hello {name}!")

if __name__ == '__main__':
    museum()

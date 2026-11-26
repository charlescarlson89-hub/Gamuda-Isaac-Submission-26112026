name= "John"
age= 25
height = 1.75
is_student = True

print(f"Name:{name},Age:{age},Height:{height},Is Student:{is_student}")

x= "Welcome"
print(x[0])
print(x[3:6])
print(x[3:])
print(x[:5])
print(x.upper())
print(x.lower())
print(len(x))
print("come"in x)
print("come1"in x)
print(x.replace("come","ly"))

x = 3
y = 2.5
print(x+y) #5.5
print(x-y) #0.5
print(x*y) #7.5
print(x/y) #1.2

import math
z=3.14159
print(round(z,2)) #3.14
print(math.floor(z)) #3
print(math.ceil(z)) #4
print(f"{z:.2f}") #3.14 

num1 = input("Enter first number:")
num2 = input("Enter second number:")
print(num1+ num2) #54
print(int(num1)+int(num2)) #9

x = "42"
y = 3.99
z= 0
print(int(x)) #42
print(int(y)) #3
print(float(x)) #42.0
print(str(y)) #'3.99'
print(bool(z)) #False
print(bool(x)) #True

age = 20
if age >= 18:
    print("You are an adult.")
else:
    print("You are not an adult.")

age = 19
if age >= 18 and age <=20:
    print("Freshman.")
elif age > 20 and age <= 22:
    print("Sophomore.")
elif age > 22:
    print("Graduate")

# and - Both sides must be True
# or - One side must be True
# not - flips True to False, False to True

age = 5
print(age > 0 and age < 10) #True
print(age > 0 or age > 10) #True
print(not(age > 3)) #False

a = 20
b =12
c = 0
d = a and b and (not c)

print(f"a = {a}") #true
print(f"b = {b}") #true
print(f"c = {c}") #false
print(f"d = a and b and (not c) {d}") #true

for i in range(1, 6):
    print(f"Number: {i}")

for i in range(1, 6):
    print(f"Number: {i}")
    if i == 3:
        break
print("loop ended.")

for i in range(1, 11):
    if i % 2 == 0:
        continue
    print(f"Odd Number: {i}")
print("loop ended.")

def greet_user():
    print("Hello, welcome to the program!")
    print("I hope you have a great day!")
    print("Let's get started.")
greet_user()
greet_user()

def calculate_area(length, width):
    area = length * width
    return area
result = calculate_area(2,3)
print(f"Area: {result}")

fruits = ["apple", "banana", "orange"]

fruits.append("grape")

fruits.insert(1, "mango")

fruits.remove("apple")

print(fruits)

print(fruits[0])

print(fruits[-1])


numbers = [3, 1, 4, 1, 5, 9, 2]

numbers.sort()

print(numbers)

numbers.reverse()

print(numbers)

print(numbers.count(1))

print(numbers.index(1))


todos = []

todos.append("Buy groceries")
todos.append("Clean the house")
todos.append("Pay bills")

print("To-Do List:")

for index, task in enumerate(todos, 1):
    print(f"{index}. {task}")


person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}
print(person["name"])
person["email"] = "alice@email.com"
print(person)
for key in person:
    print(key)
for value in person.values():
    print(value)
for key, value in person.items():
    print(f"{key}: {value}")

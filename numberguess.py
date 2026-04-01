import random as r
import math as m

x = r.randint(0,100)
print("I am thinking of a number between 1 and a 100 !!!")

while True:
    y = input("What do you think it is or say I give up so I can tell you ? : ")

    if y.lower == "I give up":
        print(x)

    z = int(y)
    if z == x:
        print("Good job, that's right!!!")
        break
    elif abs(z - x) <= 5:
        print("You're close, but not right")
    else:
        print("Not exactly, Try again .")

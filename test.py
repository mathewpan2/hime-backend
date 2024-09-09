from profanity_filter import ProfanityFilter

filter = ProfanityFilter()

while True:
    text = input("Enter text: ")
    print(filter.isProfane(text))

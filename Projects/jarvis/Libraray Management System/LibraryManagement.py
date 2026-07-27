"""
LibrarySys Simple Library Management System
Feautures:
1.Register users
2.View users
3.Remove user
4.Add books
5.Remove book
6.View books
7.Borrow books(update quantity and history)
8.Return books(updates quantity and history)
9.Donate Book
10.Save users and books in Json
11.Simple menu for navigation
"""
import os
import json
USER_FILE="users.json"
BOOK_FILE="books.json"
def load_json(file_name):
    if not os.path.exists(file_name):
        return []
    try:
        with open(file_name,'r')as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []
def save_json(file_name,data):
    with open(file_name,'w')as f:
        json.dump(data,f,indent=4)
    print(f"Saved to {file_name}")

def register_user(users):
    name=input('Enter your name:')
    if any(u['name']==name for u in users):
        print('User already registered.\n')
        return users
    user={"name":name,"borrowed_books":[]}
    users.append(user)
    save_json(USER_FILE,users)
    print(f'user: {name} registered successfully.\n')
    return users
def remove_user(users):
    if not users:
        print("No registered users.\n")
        return users
    print("----- Registered Users -----")
    for idx, user in enumerate(users, start=1):
        print(f"{idx}. {user['name']}")
    try:
        choice = int(input("Enter user number to remove: ")) - 1
        if 0 <= choice < len(users):
            if users[choice]["borrowed_books"]:
                print("User cannot be removed because they have borrowed books.\n")
                return users
            removed_user = users.pop(choice)
            save_json(USER_FILE, users)
            print(f"User '{removed_user['name']}' removed successfully.\n")
        else:
            print("Invalid user number.\n")
    except ValueError:
        print("Please enter a valid number.\n")
    return users
def view_users(users):
    if not users:
       print("No registered users.\n")
       return 
    print('-----Registered Users------')
    for idx,user in enumerate(users,start=1):
        borrowed_titles=[b['title']for b in user['borrowed_books']]
        print(f"{idx}.{user['name']}-Borrowed Books:{borrowed_titles}")
    print()
def add_book(books):
    title=input('Enter book title:')
    author=input('Enter author name:')
    try:
        quantity=int(input('Enter quantity of books:'))
    except ValueError:
        print('Invalid quantity.Setting quantity=1')
        quantity=1    
    books.append(
        {
        "title":title,
        "author":author,
        "quantity":quantity
        })
    print(books)
    save_json(BOOK_FILE,books)
    print(f'Book:{title} by {author} added with {quantity}.')
    return books
def remove_book(books):
    if not books:
        print("No books available in the library.\n")
        return books
    view_books(books)
    try:
        choice = int(input("Enter book number to remove: ")) - 1
        if 0 <= choice < len(books):
            removed_book = books.pop(choice)
            save_json(BOOK_FILE, books)
            print(f"Book '{removed_book['title']}' removed successfully.\n")
        else:
            print("Invalid book number.\n")
    except ValueError:
        print("Please enter a valid number.\n")
    return books
def view_books(books):
    if not books:
        print("No books in the library.\n")
        return books
    print('----Library Books----')
    for idx,book in enumerate(books,start=1):
            print(f"{idx}.{book['title']} by {book['author']}[Quantity:{book['quantity']}]")
    print()
    return books
def borrow_book(books,users):
    if not users:
        print('No users registered.\n')
        return books,users
    user_name=input('Enter your name:')
    find_user(users,user_name)
def find_user(users,name):
    for user in users:
        if user['name']==name:
           return user
    return None    
def borrow_book(books,users):
    if not users:
        print('No users registered.\n')
        return books,users
    user_name=input('Enter your name:')
    user=find_user(users,user_name)
    if not user:
        print('User not found.\n')
        return books,users
    view_books(books)
    if not books:
        return books,users
    try:
        choice=int(input('Enter book number.'))-1
        if 0<=choice<len(books):
            if books[choice]['quantity']>0:
                books[choice]['quantity']-=1
                user['borrowed_books'].append({
                    "title":books[choice]["title"],
                    "author":books[choice]['author']
                    })
                save_json(BOOK_FILE,books)
                save_json(USER_FILE,users)
                print(f'you borrowed {books[choice]['title']}  successfully')
            else:
               print('Sorry,out of stock')
        else:
            print('Invalid book number')
    except ValueError:
        print("Please enter valid number")
    return books,users
def return_book(books,users):
    user_name=input('Enter your name:')
    user=find_user(users,user_name)
    if not user:
        print('User not found')
        return books,users
    if not user['borrowed_books']:
        print('You have no books.\n')
        return books,users
    print('\n ------Borrowed Books----')
    for idx,book in enumerate(user['borrowed_books'],start=1):
        print(f"{idx}.book['title'] by {book['author']}")
    try:
        choice=int(input('Enter book number to return:'))-1
        if 0<=choice <len(user['borrowed_books']):
            returning_book=user['borrowed_books'].pop(choice)
            for b in books:
              if b['title']==returning_book['title']and b['author']==returning_book['author']:
                b['quantity']+=1
                break
            save_json(BOOK_FILE,books)
            save_json(USER_FILE,users)
            print("you returned {returning_book['title']}successfully.")
        else:
            print("Invalid choice\n")
    except ValueError:
        print('Please enter a valid number\n')
    return books,users
def donate_book(books):
    title = input("Enter book title: ")
    author = input("Enter author name: ")
    try:
        quantity = int(input("Enter quantity to donate: "))
    except ValueError:
        print("Invalid quantity. Setting quantity = 1")
        quantity = 1
    for book in books:
        if (book["title"].lower() == title.lower() and
                book["author"].lower() == author.lower()):
            book["quantity"] += quantity
            save_json(BOOK_FILE, books)
            print(f"Thank you! {quantity} copy/copies of '{title}' donated successfully.\n")
            return books
    books.append({
        "title": title,
        "author": author,
        "quantity": quantity
    })
    save_json(BOOK_FILE, books)
    print(f"Thank you! '{title}' added to the library with {quantity} copy/copies.\n")
    return books
def main():
    users=load_json(USER_FILE)
    books=load_json(BOOK_FILE)
    while True:
        print("====LibrarySys Menu=====")
        print("1.Register User")
        print("2.View Users")
        print("3.Add Book")
        print("4.View Books")
        print("5.Borrow Book")
        print("6.Return Book")
        print("7.Exit")
        choice=input("Choose an option:")
        print("you entered:",choice)
        if choice=="1":
          users=register_user(users)
        elif choice=="2":
          view_users(users)
        elif choice=="3":
          users=remove_user(users)
        elif choice=="4":
          print("books before add_book",books)
          books=add_book(books)
        elif choice=="5":
           books=remove_book(books)
        elif choice=="6":
          books=view_books(books)
        elif choice=="7":
          books, users=borrow_book(books,users)
        elif choice=="8":
            books,users=return_book(books,users)
        elif choice=="9":
            books=donate_book(books)
        elif choice=="10":
          print("Existing LibrarySys... Goodbye!")
          break
        else:
          print("Invalid choice,please try again.\n")
main()
    
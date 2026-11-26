pending = {}
done = {}
next_task_id = 1


def show_tasks():
    for title, tasks in (("Pending Tasks:", pending), ("Done Tasks:", done)):
        print(title)
        if not tasks:
            print("No tasks yet.")
        for index, task in enumerate(tasks.values(), 1):
            print(f"{index}. {task}")


def add_task():
    global next_task_id
    task = input("Enter a new task: ").strip()
    if task:
        pending[next_task_id] = task
        next_task_id += 1
        print("Task added.")


def complete_task():
    try:
        index = int(input("Enter the number of the task you finished: ")) - 1
    except ValueError:
        print("Invalid task number.")
        return
    if 0 <= index < len(pending):
        task_id = list(pending)[index]
        done[task_id] = pending.pop(task_id)
        print("Task completed.")
    else:
        print("Invalid task number.")


def show_summary():
    print("--- Summary ---")
    print(f"Pending : {len(pending)} tasks")
    print(f"Done    : {len(done)} tasks")


while True:
    print("\n1. Show tasks\n2. Add a task\n3. Complete a task\n4. Show summary\n5. Exit")
    choice = input("Choose an option: ")
    if choice == "1":
        show_tasks()
    elif choice == "2":
        add_task()
    elif choice == "3":
        complete_task()
    elif choice == "4":
        show_summary()
    elif choice == "5":
        break
    else:
        print("Invalid option.")

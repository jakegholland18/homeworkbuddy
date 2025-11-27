# main.py

import modules.math_helper as math_helper
import modules.text_helper as text_helper
import modules.question_helper as question_helper
import modules.science_helper as science_helper
import modules.bible_helper as bible_helper
import modules.history_helper as history_helper
import modules.writing_helper as writing_helper
import modules.study_helper as study_helper
import modules.apologetics_helper as apologetics_helper
import modules.investment_helper as investment_helper
import modules.money_helper as money_helper


def welcome_message():
    print("=====================================")
    print("       WELCOME TO HOMEWORK BUDDY      ")
    print("=====================================")
    print("An AI-powered tutor for ALL subjects!")
    print("Covers Math • Science • Bible • Reading")
    print("History • Writing • Study Tools & more")
    print("=====================================\n")


if __name__ == "__main__":
    welcome_message()

    # -------------------------
    # Ask for student's grade FIRST
    # -------------------------
    grade_level = input("What grade are you in (1–12)? ").strip()

    print(f"\nGreat! I will teach at a grade {grade_level} level.\n")

    # -------------------------
    # MAIN MENU LOOP
    # -------------------------
    while True:
        print("\nChoose a subject to get help with:")
        print("1 - Math Helper (All math features)")
        print("2 - Text / Reading Helper")
        print("3 - General Question Helper")
        print("4 - Science Helper")
        print("5 - Bible Learning Module")
        print("6 - History Helper")
        print("7 - Writing / Essay Helper")
        print("8 - Study Tools (Quizzes + Flashcards)")
        print("9 - Apologetics Helper")
        print("10 - Investment Helper")
        print("11 - Accounting / Money Helper")
        print("0 - Exit")

        choice = input("Enter your choice: ").strip()

        # --------------------------------------------------
        # MATH HELPER
        # --------------------------------------------------
        if choice == "1":
            print("\n--- MATH HELPER ---")
            print("a - Basic Math")
            print("b - Explain ANY Math Concept")
            print("c - Solve ANY Math Problem")
            print("d - Generate a Math Quiz")

            sub = input("Choose an option (a/b/c/d): ").strip().lower()

            if sub == "a":
                a = float(input("Enter first number: "))
                b = float(input("Enter second number: "))
                print("Addition:", math_helper.add_numbers(a, b))
                print("Subtraction:", math_helper.subtract_numbers(a, b))
                print("Multiplication:", math_helper.multiply_numbers(a, b))
                print("Division:", math_helper.divide_numbers(a, b))

            elif sub == "b":
                topic = input("Enter a math concept: ")
                print("\n--- Math Concept Explanation ---")
                print(math_helper.explain_math(topic, grade_level))

            elif sub == "c":
                problem = input("Enter the math problem: ")
                print("\n--- Step-by-Step Solution ---")
                print(math_helper.solve_math_problem(problem, grade_level))

            elif sub == "d":
                topic = input("What math topic should the quiz cover? ")
                print("\n--- Math Quiz ---")
                print(math_helper.generate_math_quiz(topic, grade_level))

            else:
                print("Invalid math option.")

        # --------------------------------------------------
        # TEXT / READING
        # --------------------------------------------------
        elif choice == "2":
            text = input("Enter text to summarize: ")
            print("\n--- Summary ---")
            print(text_helper.summarize_text(text, grade_level))

        # --------------------------------------------------
        # GENERAL QUESTIONS
        # --------------------------------------------------
        elif choice == "3":
            question = input("Enter your question: ")
            print("\n--- Answer ---")
            print(question_helper.answer_question(question, grade_level))

        # --------------------------------------------------
        # SCIENCE
        # --------------------------------------------------
        elif choice == "4":
            topic = input("Enter your science topic/question: ")
            print("\n--- Science Lesson ---")
            print(science_helper.explain_science(topic, grade_level))

        # --------------------------------------------------
        # BIBLE
        # --------------------------------------------------
        elif choice == "5":
            topic = input("Enter Bible topic or passage: ")
            print("\n--- Bible Lesson ---")
            print(bible_helper.bible_lesson(topic, grade_level))

        # --------------------------------------------------
        # HISTORY
        # --------------------------------------------------
        elif choice == "6":
            topic = input("Enter a history topic: ")
            print("\n--- History Lesson ---")
            print(history_helper.explain_history(topic, grade_level))

        # --------------------------------------------------
        # WRITING
        # --------------------------------------------------
        elif choice == "7":
            task = input("What do you need help writing? ")
            print("\n--- Writing Help ---")
            print(writing_helper.help_write(task, grade_level))

        # --------------------------------------------------
        # STUDY TOOLS
        # --------------------------------------------------
        elif choice == "8":
            topic = input("Create study tools for which topic? ")
            print("\n--- Quiz ---")
            print(study_helper.generate_quiz(topic, grade_level))
            print("\n--- Flashcards ---")
            print(study_helper.flashcards(topic, grade_level))

        # --------------------------------------------------
        # APOLOGETICS
        # --------------------------------------------------
        elif choice == "9":
            question = input("Enter your apologetics question: ")
            print("\n--- Apologetics Answer ---")
            print(apologetics_helper.apologetics_answer(question, grade_level))

        # --------------------------------------------------
        # INVESTMENT HELPER
        # --------------------------------------------------
        elif choice == "10":
            topic = input("What investment topic do you want to learn about? ")
            print("\n--- Investing Lesson ---")
            print(investment_helper.explain_investing(topic, grade_level))
            print("\n--- Investing Quiz ---")
            print(investment_helper.investment_quiz(topic, grade_level))

        # --------------------------------------------------
        # ACCOUNTING / MONEY
        # --------------------------------------------------
        elif choice == "11":
            print("\n--- Money & Accounting Helper ---")
            print("a - Learn a money topic")
            print("b - Solve an accounting problem")
            print("c - Generate an accounting quiz")

            sub = input("Choose (a/b/c): ").strip().lower()

            if sub == "a":
                topic = input("What money topic do you want to learn? ")
                print(money_helper.explain_money(topic, grade_level))

            elif sub == "b":
                problem = input("Enter your accounting problem: ")
                print(money_helper.solve_accounting_problem(problem, grade_level))

            elif sub == "c":
                topic = input("Quiz on what accounting topic? ")
                print(money_helper.accounting_quiz(topic, grade_level))

            else:
                print("Invalid option.")

        # --------------------------------------------------
        # EXIT
        # --------------------------------------------------
        elif choice == "0":
            print("\nGoodbye! Keep learning!")
            break

        else:
            print("Invalid choice, try again.")

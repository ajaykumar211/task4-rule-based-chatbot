import json
import re
import difflib
import os
import random
import sys
from datetime import datetime, timedelta, timezone

FAQ_FILE = "faq.json"
LOG_FILE = "chat_log.txt"
IST = timezone(timedelta(hours=5, minutes=30))  # hours are stated in IST


# ---------- Colors (ANSI) ----------
os.system("")  # lets ANSI colors work in older Windows terminals
USE_COLOR = sys.stdout.isatty()  # no colors when output is not a terminal
CYAN = "\033[96m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""

# ---------- Load data (with error handling) ----------
try:
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    greetings = data["greetings"]
    faqs = data["faqs"]
except FileNotFoundError:
    print("Error: faq.json was not found. Keep it in the same folder as chatbot.py.")
    raise SystemExit
except (json.JSONDecodeError, KeyError) as err:
    print("Error: faq.json is not valid:", err)
    raise SystemExit

EXIT_WORDS = ("bye", "exit", "quit")
YES_WORDS = ("yes", "y", "yeah", "yep", "sure", "ok", "okay")

STOP_WORDS = {
    "a", "an", "the", "is", "are", "do", "does", "i", "my", "me", "you",
    "your", "to", "of", "and", "what", "how", "can", "for", "in", "on",
    "will", "should", "it", "we", "when", "where", "which"
}

# ---------- Regex intents: name -> (pattern, answer) ----------
INTENTS = {
    "hours": (
        r"\b(hours?|timings?|opens?|opening|closes?|closing|schedule)\b",
        "We operate Monday through Friday from 9:00 AM to 6:00 PM IST.",
    ),
    "days": (
        r"\b(working days|weekends?|holidays?|saturday|sunday)\b",
        "We operate Monday through Friday.",
    ),
    "contact": (
        r"\b(contact|email|mail|support|phone|reach|help ?desk)\b",
        "Please use the help or support options in your Student Workspace on the Datheon website.",
    ),
    "certificate": (
        r"\b(certificates?|certification|credentials?)\b",
        "Certificates are reviewed and issued within 3-5 business days after your code review.",
    ),
    "submit": (
        r"\b(submit|submission|upload|github|repository|repo)\b",
        "You can submit your public GitHub repository link through your Student Workspace.",
    ),
    "deadline": (
        r"\b(deadline|due date|last date|due)\b",
        "Please complete and submit your tasks within the time shown on your dashboard.",
    ),
    "fee": (
        r"\b(fees?|cost|price|charges?|payment|is it free|free of charge)\b",
        "The evaluation is free. Step 3 on your dashboard is marked Zero Evaluation Fee.",
    ),
    "language": (
        r"\b(python|language|programming)\b",
        "Use Python 3 for this task, along with the re and json modules.",
    ),
    "tasks": (
        r"\b(tasks?|dashboard)\b",
        "Log in to the Datheon website and open the Training Dashboard. Your tasks are listed there with their requirements.",
    ),
}

user_name = "friend"
state = "greeting"  # greeting -> intent -> resolution (or fallback) -> exit


def set_state(new_state):
    """Track the conversation stage and write each change to the log."""
    global state
    if new_state != state:
        log("State", f"{state} -> {new_state}")
        state = new_state


# ---------- Output helpers (print + log) ----------
def log(speaker, text):
    """Append one line to the conversation log. Never crashes the bot."""
    try:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {speaker}: {text}\n")
    except OSError:
        pass

def say(text):
    print(f"{CYAN}Bot: {text}{RESET}")
    log("Bot", text.replace("\n", " | "))


def ask(prompt="You: "):
    reply = input(f"{YELLOW}{prompt}{RESET}")
    log("User", reply)
    return reply

def is_yes(text):
    return normalize(text) in YES_WORDS


# ---------- Text helpers ----------
def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def get_keywords(text):
    return {w for w in normalize(text).split() if w not in STOP_WORDS}


def is_greeting(text):
    """True for short greetings such as 'hello' or 'hi there'."""
    clean = normalize(text)
    if len(clean.split()) > 3 or find_intents(clean):
        return False
    return any(clean == normalize(g) or clean.startswith(normalize(g) + " ")
               for g in greetings)


def extract_name(text):
    """Return a name if the text looks like one, otherwise None."""
    cleaned = re.sub(r"^(my name is|name is|i am|im|this is|call me)\s+", "",
                     normalize(text))
    words = cleaned.split()
    if not 1 <= len(words) <= 3 or not all(w.isalpha() for w in words):
        return None
    if cleaned in ("help", "yes", "no") or cleaned in EXIT_WORDS:
        return None
    if is_greeting(cleaned) or find_intents(cleaned) or small_talk(cleaned):
        return None
    return cleaned.title()


# ---------- Time features ----------
def time_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def open_status():
    """Say whether we are open right now (Mon-Fri, 9 AM - 6 PM IST)."""
    now = datetime.now(IST)
    weekday, hour = now.weekday(), now.hour  # Monday = 0
    if weekday < 5 and 9 <= hour < 18:
        return "We are open right now."
    if weekday < 5 and hour < 9:
        when = "today"
    elif weekday < 4:
        when = "tomorrow"
    else:
        when = "Monday"
    return f"We are closed right now. We open {when} at 9:00 AM."


# ---------- Matching ----------
def find_intents(text):
    """Return [(intent_name, answer), ...] for every regex that matches."""
    clean = normalize(text)
    return [(name, answer) for name, (pattern, answer) in INTENTS.items()
            if re.search(pattern, clean)]


def find_best_faq(text):
    user_words = get_keywords(text)
    best_score, best_answer = 0, None
    for item in faqs:
        score = len(user_words & get_keywords(item["question"]))
        if score > best_score:
            best_score, best_answer = score, item["answer"]
    return best_score, best_answer


def add_status(intent_names, reply):
    """Add the open/closed line when the hours topic was answered."""
    if "hours" in intent_names:
        reply += "\n" + open_status()
    return reply


def get_reply(text):
    """Return an answer string, or None when the bot does not know."""
    found = find_intents(text)
    names = [n for n, _ in found]
    answers = [a for _, a in found]
    faq_score, faq_answer = find_best_faq(text)

    if len(answers) >= 2:
        return add_status(names, "\n".join(answers))
    if faq_score >= 2:
        return faq_answer
    if len(answers) == 1:
        return add_status(names, answers[0])
    if faq_score == 1:
        return faq_answer
    return None


def suggest_question(text):
    """Return the FAQ whose words are closest to the text (typo tolerant)."""
    user_words = get_keywords(text)
    best_item, best_score = None, 0
    for item in faqs:
        faq_words = list(get_keywords(item["question"]))
        score = sum(1 for w in user_words
                    if difflib.get_close_matches(w, faq_words, n=1, cutoff=0.8))
        if score > best_score:
            best_item, best_score = item, score
    return best_item


# ---------- Learning ----------
def save_faqs():
    try:
        with open(FAQ_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def learn_new_answer(question):
    if not get_keywords(question):
        say("I can't learn from that. Try a longer question.")
        return
    say("I don't know that yet. Want to teach me the answer? (yes/no)")
    if not is_yes(ask()):
        say("No problem. Ask me something else.")
        return
    say("Great! Type the answer, or press Enter to cancel:")
    answer = ask().strip()
    if answer == "":
        say("Cancelled. Nothing was saved.")
        return
    faqs.append({"question": question.strip(), "answer": answer})
    if save_faqs():
        say("Thanks, " + user_name + "! I learned it and saved it to faq.json.")
    else:
        say("I learned it for now, but could not save it to faq.json.")


JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the Python programmer wear glasses? Because he couldn't C!",
    "There are 10 kinds of people: those who understand binary and those who don't.",
]


def small_talk(text):
    """Handle thanks, time, date, jokes and chit-chat. Return reply or None."""
    if re.search(r"\b(thanks?|thank you|thx)\b", text):
        return f"You're welcome, {user_name}! Anything else I can help with?"
    if re.search(r"\b(who are you|what are you|what can you do|about you)\b", text):
        return ("I'm a rule-based internship assistant built in Python with the "
                "re and json modules. Type 'help' to see what I can answer.")
    if re.search(r"\b(how are you|hows it going)\b", text):
        return "I'm doing great, thanks for asking! How can I help you?"
    if re.search(r"\b(what time is it|current time|time now|time is it)\b", text):
        return "It is " + datetime.now().strftime("%I:%M %p") + "."
    if re.search(r"\b(todays date|date today|what day is it|what is the date)\b", text):
        return "Today is " + datetime.now().strftime("%A, %d %B %Y") + "."
    if re.search(r"\b(joke|funny)\b", text):
        return random.choice(JOKES)
    return None


def show_help():
    say("I can help with these topics:\n"
        "  1. Business hours and working days (and if we're open now)\n"
        "  2. Contact and support\n"
        "  3. Certificates\n"
        "  4. Project submission and GitHub\n"
        "  5. Deadlines, fees and tasks\n"
        "  6. Python and the tools used\n"
        "  7. About Task 4 and the sample dataset\n"
        "  8. How this chatbot works (fallback, multi intent, learning)\n"
        "Fun extras: ask for the time, today's date, a joke, or say thanks.\n"
        "Commands: 'help', and 'bye' / 'exit' / 'quit' to leave.\n"
        "If I don't know something, I can learn it from you!")
    lines = ["Questions you can ask me:"]
    for number, item in enumerate(faqs, start=1):
        lines.append(f"  {number}. {item['question']}")
    say("\n".join(lines))


# ---------- Main program ----------
def main():
    global user_name

    set_state("greeting")
    say(f"{time_greeting()}! I'm your internship assistant. What's your name?")
    try:
        name = ask().strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBot: Goodbye!")
        return

    if normalize(name) in EXIT_WORDS:
        set_state("exit")
        say("Goodbye! Have a great day.")
        return

    pending = None  # a question typed instead of a name is answered first
    found_name = extract_name(name)
    if found_name:
        user_name = found_name
        say(f"Nice to meet you, {user_name}! Ask me anything, or type 'help'. "
            "Type 'bye', 'exit' or 'quit' to leave.")
    else:
        say("No problem, we can skip the introductions. Ask me anything, "
            "or type 'help'. Type 'bye', 'exit' or 'quit' to leave.")
        if name:
            pending = name

    set_state("intent")

    while True:
        if pending is not None:
            user, pending = pending, None
        else:
            try:
                user = ask()
            except (EOFError, KeyboardInterrupt):
                print("\nBot: Goodbye!")
                break

        text = normalize(user)
        set_state("intent")

        if text == "":
            say("Please type something so I can help.")
            continue

        # Exit: exact words, or a close typo after a yes/no confirmation
        leave = text in EXIT_WORDS
        if not leave:
            close = difflib.get_close_matches(text, EXIT_WORDS, n=1, cutoff=0.8)
            if close:
                say(f'Did you mean "{close[0]}"? Leave the chat? (yes/no)')
                if is_yes(ask()):
                    leave = True
                else:
                    say("Okay, let's keep chatting.")
                    continue
        if leave:
            set_state("exit")
            say(f"Goodbye, {user_name}! Have a great day.")
            break

        if text == "help":
            show_help()
            continue

        if is_greeting(user):
            say(f"{time_greeting()}, {user_name}! How can I help you today?")
            continue

        talk = small_talk(text)
        if talk:
            set_state("resolution")
            say(talk)
            continue

        reply = get_reply(user)
        if reply:
            set_state("resolution")
            say(reply)
            continue

        # Not understood: offer a suggestion, then offer to learn
        set_state("fallback")
        suggestion = suggest_question(user)
        if suggestion:
            say(f"Did you mean: \"{suggestion['question']}\" (yes/no)")
            if is_yes(ask()):
                set_state("resolution")
                say(suggestion["answer"])
                continue
        learn_new_answer(user)


main()
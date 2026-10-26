\# Rule-Based Interactive Terminal Chatbot



A rule-based internship assistant that runs in the terminal. It is built with Python 3 using the `re` and `json` modules, plus `difflib`, `datetime` and `random` from the standard library. No AI or machine-learning services are used.



\## Features



\### Required by the task

\- \*\*Regex intent matching:\*\* patterns catch many wordings, so `timings`, `open` and `closing` all lead to the business hours answer.

\- \*\*FAQ dataset from JSON:\*\* questions and answers are loaded from `faq.json`.

\- \*\*Input normalization:\*\* text is lowercased and stripped of extra spaces and punctuation.

\- \*\*Multi-intent answers:\*\* `hours and contact email` returns both answers.

\- \*\*Conversation flow:\*\* greeting, intent identification, resolution, exit. Each state change is written to the log.

\- \*\*Graceful fallback:\*\* unknown questions get a suggestion or an offer to learn, never a crash.

\- \*\*Clean exit:\*\* `bye`, `exit` or `quit`.

\- \*\*Error handling:\*\* a missing or invalid `faq.json`, empty input, and Ctrl+C are all handled.



\### Extra features

\- Asks for your name and greets you by name, with a time-based greeting.

\- Tells you if the business is open right now (Monday to Friday, 9 AM to 6 PM IST).

\- "Did you mean...?" suggestions that tolerate typos.

\- Learns new answers from the user and saves them to `faq.json`.

\- `help` command with topics and a self-updating list of all known questions.

\- Typo-tolerant exit that asks for confirmation (for example `byye`).

\- Small talk: thanks, "who are you", the current time and date, and jokes.

\- Colored terminal output.

\- Conversation log in `chat\_log.txt`, created automatically while chatting.



\## Project files



| File | Purpose |

|---|---|

| `chatbot.py` | The chatbot program |

| `faq.json` | Greetings and FAQ dataset |

| `README.md` | Project documentation |



\## How to run



1\. Install Python 3 from python.org.

2\. Keep `chatbot.py` and `faq.json` in the same folder.

3\. Open a terminal in that folder and run:



```

python chatbot.py

```



Type `help` to see what the bot can answer, and `bye`, `exit` or `quit` to leave.



\## Sample conversation



```

Bot: Good evening! I'm your internship assistant. What's your name?

You: Ajay 
 
Bot: Nice to meet you, Ajay! Ask me anything, or type 'help'. Type 'bye', 'exit' or 'quit' to leave.

You: what are your timings

Bot: We operate Monday through Friday from 9:00 AM to 6:00 PM IST.

We are open right now.

You: hours and contact email

Bot: We operate Monday through Friday from 9:00 AM to 6:00 PM IST.

Please use the help or support options in your Student Workspace on the Datheon website.

We are open right now.

You: when certifcate

Bot: Did you mean: "When will I receive my certificate?" (yes/no)

You: yes

Bot: Certificates are reviewed and issued within 3-5 business days after your code review.

You: bye

Bot: Goodbye, Ajay! Have a great day.

```



\## How it works



1\. Input is normalized.

2\. Exit words end the program. A near-miss such as `byye` asks for confirmation first.

3\. Greetings and small talk are handled next.

4\. Regex patterns find every topic in the message.

5\. If no topic matches strongly, the FAQ with the most shared keywords is used.

6\. If nothing matches, the bot suggests a similar question or offers to learn the answer.



\## Author



ajay


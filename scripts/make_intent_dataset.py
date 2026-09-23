"""Generates data/intents.csv: hand-written seed queries per intent plus
light paraphrase augmentation (prefix/suffix variants).  Re-run to rebuild.
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

random.seed(7)
OUT = Path(__file__).resolve().parent.parent / "data" / "intents.csv"

SEEDS = {
"coding": [
 "Why does my React useEffect run twice on mount",
 "Fix this Python TypeError: unsupported operand type(s) for +: 'int' and 'str'",
 "Write a function that reverses a linked list in Java",
 "How do I set up a virtual environment with venv",
 "Convert this for loop into a list comprehension",
 "My Flask app returns 404 for every route, what is wrong",
 "Explain the difference between async and await in JavaScript",
 "Write a SQL query to get the top 5 customers by total order value",
 "How to merge two branches in git without a merge commit",
 "Debug this segmentation fault in my C program",
 "What does the 'static' keyword do in C++",
 "Write unit tests for this login function using pytest",
 "Refactor this class to use dependency injection",
 "How do I read a CSV file into a pandas DataFrame",
 "Implement binary search in Go",
 "Why is my Docker container exiting immediately",
 "Write a regex that matches Indian phone numbers",
 "How to handle CORS errors in an Express server",
 "Optimize this nested loop, it is O(n^2)",
 "What is the difference between let, const and var",
 "Add error handling to this fetch call",
 "Write a bash script that renames all .txt files to .md",
 "How do I connect to MongoDB from Node.js",
 "My Streamlit app reruns the whole script on every click, how to cache",
 "Implement a LRU cache in Python",
 "Explain this stack trace from Spring Boot",
 "Create a REST endpoint that returns JSON in FastAPI",
 "How do I use TypeScript generics with interfaces",
 "Write a Dockerfile for a Django project",
 "Fix the indentation error in this code block",
 "How to schedule a cron job that runs every 15 minutes",
 "Write a Kotlin data class for a user profile",
 "Why does npm install fail with EACCES permission denied",
 "Implement quicksort and explain its complexity",
 "How to parse JSON in Rust with serde",
 "Write a Python decorator that logs function execution time",
 "My git push is rejected because the remote contains work I do not have",
 "How do I make an HTTP POST request with requests in Python",
 "Convert this callback code to promises",
 "Write a C function to check if a number is prime",
 "What is a race condition and how do I avoid it with mutexes",
 "Set up ESLint and Prettier in a Next.js project",
 "Write a migration to add an index on the email column",
 "How do I deploy a Node app on an Ubuntu VPS with pm2",
 "Explain what this lambda expression does",
],
"writing": [
 "Write a 1000-word essay on climate feedback loops",
 "Draft a cover letter for a software engineering internship",
 "Write a blog post about the benefits of morning routines",
 "Compose a heartfelt wedding toast for my best friend",
 "Rewrite this paragraph to sound more formal",
 "Write a short story about a lighthouse keeper who finds a message in a bottle",
 "Draft an email to my professor asking for a deadline extension",
 "Write a product description for a handmade leather wallet",
 "Create a LinkedIn post announcing my new job",
 "Write a poem about monsoon in Hyderabad",
 "Summarize this article in three paragraphs for a newsletter",
 "Write the introduction chapter for my thesis on renewable energy",
 "Draft a press release for our app launch",
 "Write a persuasive speech on why students should learn to code",
 "Help me write a eulogy for my grandfather",
 "Write a letter of recommendation for my intern",
 "Compose a polite complaint email to my landlord about the leaking roof",
 "Write a 500-word reflection on what I learned this semester",
 "Draft the about-us page for a startup that sells organic tea",
 "Write a motivational message for my team before the hackathon",
 "Turn these bullet points into a well-structured report",
 "Write a movie review of a sci-fi film I just watched",
 "Write a bedtime story for a five year old about a brave turtle",
 "Draft an apology email for missing the client meeting",
 "Write a travel blog entry about a weekend in Goa",
 "Create a script for a two-minute YouTube intro video",
 "Write an op-ed on the future of remote work",
 "Polish this abstract so it reads well for a journal submission",
 "Write song lyrics about leaving home for college",
 "Draft a resignation letter that keeps things friendly",
 "Write a detailed proposal for a campus recycling program",
 "Write a haiku about coffee",
 "Help me write a bio for my conference speaker profile",
 "Expand this outline into a full article on sleep hygiene",
 "Write a welcome email sequence for new subscribers",
 "Draft a toast for my parents' anniversary dinner",
 "Write a long-form explainer on how vaccines work for a general audience",
 "Compose a thank-you note to my mentor",
 "Write a fictional dialogue between two rival chefs",
 "Write a personal statement for a masters application",
 "Make this paragraph more concise without losing meaning",
 "Write an engaging opening paragraph for a mystery novel",
 "Draft meeting minutes from these notes",
 "Write a case study about how our team reduced churn",
 "Write a limerick about a cat who codes",
],
"search": [
 "What is the current inflation rate in India",
 "Who won the Formula 1 race last weekend",
 "What is the latest version of Python",
 "When is the next solar eclipse visible from India",
 "What is the population of Bangalore in 2026",
 "Who is the CEO of OpenAI right now",
 "What are today's headlines about the stock market",
 "How much does a Tesla Model 3 cost in India",
 "What time does the Apple event start today",
 "Is the Bangalore metro purple line open on Sundays",
 "What is the weather in Chennai tomorrow",
 "Latest news on the ISRO Gaganyaan mission",
 "Who won the Nobel Prize in Physics this year",
 "What is the exchange rate of USD to INR today",
 "When was the Eiffel Tower built",
 "What is the capital of Kazakhstan",
 "How tall is Mount Kilimanjaro",
 "Which teams are in the IPL final this season",
 "What is the release date of the next iPhone",
 "What are the current RBI repo rate figures",
 "Find recent papers on retrieval-augmented generation",
 "What happened in the tech industry this week",
 "Who directed the movie Oppenheimer",
 "What is the boiling point of ethanol",
 "How many moons does Jupiter have",
 "What is the GDP of Japan",
 "Look up the opening hours of the Bangalore Palace",
 "What is the latest Android version called",
 "Which company acquired Figma",
 "How far is the moon from Earth",
 "What is the score of the India vs Australia match",
 "When does daylight saving time end in the US this year",
 "What is the current price of Bitcoin",
 "Who is the president of France",
 "What are the symptoms of dengue fever",
 "Where is the 2028 Olympics being held",
 "What is the speed of light in km per second",
 "Search for the best-rated laptops under 60000 rupees",
 "What year did India win its first cricket World Cup",
 "What is the tallest building in the world right now",
 "What are the visa requirements for Indians travelling to Japan",
 "Give me the latest unemployment statistics for the US",
 "What is the atomic number of tungsten",
 "Has the new Tamil Nadu EV policy been announced yet",
 "What is the current world record for the 100m sprint",
],
"reasoning": [
 "Two trains leave stations 300 km apart at 60 and 90 km/h toward each other, when do they meet",
 "If all bloops are razzies and all razzies are lazzies, are all bloops lazzies",
 "A bat and a ball cost 1.10 in total, the bat costs one more than the ball, what does the ball cost",
 "Solve for x: 3x + 7 = 2x - 5",
 "Should I take the job with higher pay or the one with better learning, think it through",
 "What is the probability of getting two heads in three coin tosses",
 "Explain step by step why the sky is blue",
 "If I invest 10000 at 8 percent compounded annually, how much after 5 years",
 "Which is heavier, a kilogram of feathers or a kilogram of steel, and why do people get it wrong",
 "Walk me through the logic of the Monty Hall problem",
 "A farmer has 17 sheep, all but 9 die, how many are left",
 "Compare the pros and cons of renting versus buying a house",
 "How many times do the hands of a clock overlap in 24 hours",
 "If a train catches up to another train, how do I set up the equations",
 "Prove that the square root of 2 is irrational",
 "What is the next number in the sequence 2, 6, 12, 20, 30",
 "Is it rational to buy lottery tickets, argue both sides",
 "Three boxes are labelled wrong, how many draws do I need to relabel them correctly",
 "Explain why dividing by zero is undefined",
 "Estimate how many piano tuners there are in Chicago",
 "Which is a better deal, 30 percent off or buy two get one free",
 "Help me think through whether to drop this course",
 "A rope ladder hangs over a ship, the tide rises 1 metre, how many rungs go under water",
 "Derive the quadratic formula from completing the square",
 "If it takes 5 machines 5 minutes to make 5 widgets, how long for 100 machines to make 100 widgets",
 "What is the flaw in this argument: all birds fly, penguins are birds, so penguins fly",
 "How would you decide between two equally qualified job candidates",
 "Reason about whether P equals NP matters for everyday software",
 "Calculate the area of a triangle with sides 5, 6 and 7",
 "I have 3 red and 5 blue socks in a drawer, how many must I pull to guarantee a pair",
 "Explain the trolley problem and the main positions on it",
 "How many handshakes happen if 12 people each shake hands once",
 "Break down whether a startup should raise money now or bootstrap",
 "Why does compound interest grow faster than simple interest",
 "A man walks 3 km north then 4 km east, how far is he from the start",
 "What is wrong with this proof that 1 equals 2",
 "Reason step by step: is it better to pay off debt or invest first",
 "If today is Tuesday, what day is it 100 days from now",
 "Explain the logic behind the birthday paradox",
 "How would you fairly divide a cake among three people",
 "Think through the trade-offs of a four-day work week",
 "Find the sum of all integers from 1 to 200",
 "Two fathers and two sons go fishing and catch three fish, one each, how",
 "Is this syllogism valid: some cats are black, all black things are dark, so some cats are dark",
 "Estimate the number of cars in Bangalore with reasoning",
],
"multimodal": [
 "Compare these two chart screenshots and tell me which trend is stronger",
 "What is written on this whiteboard photo",
 "Describe what is in this image",
 "Read the text in this scanned receipt and total it",
 "Look at this UI mockup and suggest improvements",
 "What breed is the dog in this picture",
 "Extract the table from this screenshot into CSV",
 "Is this plant in the photo healthy or diseased",
 "Identify the landmark in this photo",
 "What does this error screenshot say and how do I fix it",
 "Translate the menu in this image to English",
 "Analyze this graph image and summarize the key finding",
 "Describe the outfit in this photo and suggest matching shoes",
 "What is the diagram in this picture showing",
 "Read the handwriting in this note and type it out",
 "Count the number of people in this image",
 "Which of these two logo designs looks more professional",
 "Explain the circuit in this photo",
 "What ingredients can you see in this fridge photo",
 "Check this screenshot of my code for bugs",
 "Caption this image for Instagram",
 "What color is the car in the picture",
 "Look at this floor plan image and estimate the room sizes",
 "Turn this photographed math problem into text and solve it",
 "Is the text in this poster image readable enough",
 "Describe the mood of this painting",
 "What does the label on this medicine bottle photo say",
 "Analyze this X-ray image for anything unusual",
 "Compare these two product photos, which has better lighting",
 "What is the make and model of the bike in this image",
 "Detect the objects in this street photo",
 "What emotion is the person in this picture showing",
 "Read the number plate from this photo",
 "Find the typo in this screenshot of my slide",
 "Describe the architecture style of the building in the photo",
 "Look at this chest of drawers photo and tell me how to fix the drawer",
 "What is the graph in this image plotting on the y axis",
 "Summarize the infographic in this picture",
 "Which of these two selfies should I use for my profile",
 "Is the wiring in this photo done safely",
 "Identify the bird in this image",
 "Transcribe the equation from this photo into LaTeX",
 "Look at this screenshot and tell me which button to click next",
 "What dish is shown in this photo and how is it made",
 "Read the expiry date from this photo of the packet",
],
}

from _extra_seeds import EXTRA
for _k in SEEDS:
    SEEDS[_k] += EXTRA[_k]

PREFIX = ["", "", "", "Can you ", "Please ", "Hey, ", "Quick one: ", "I need help: ", "Could you "]
SUFFIX = ["", "", "", " please", "?", ".", " asap", " thanks"]


def lower_first(s):
    return s[0].lower() + s[1:] if s else s


rows = []
for intent, seeds in SEEDS.items():
    seeds = seeds[:]
    random.shuffle(seeds)
    n_test = round(len(seeds) * 0.2)
    for k, s in enumerate(seeds):
        # split is decided per SEED so paraphrases of a test query never leak into train
        split = "test" if k < n_test else "train"
        gid = f"{intent}-{k:03d}"
        rows.append((s, intent, gid, split))
        seen = {s}
        tries = 0
        while len(seen) < 3 and tries < 20:
            tries += 1
            p, q = random.choice(PREFIX), random.choice(SUFFIX)
            v = (p + (lower_first(s) if p else s) + q).strip()
            if v not in seen:
                seen.add(v)
                rows.append((v, intent, gid, split))

random.shuffle(rows)
OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["text", "intent", "group", "split"])
    w.writerows(rows)
print(f"wrote {len(rows)} rows to {OUT}")

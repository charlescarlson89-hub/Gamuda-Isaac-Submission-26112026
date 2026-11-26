# Lesson catch-up

## Python foundations · slides 13, 16, 23–25

Run one Python file at a time from the `05-python` folder. `Python Example.py` includes the corrected Boolean and dictionary examples. The temperature converter, list to-do manager and dictionary to-do manager have separate entry files.

## API fetching · slides 11–12

Run `npm ci`, then `npm run dev` from `05.2-api-fetching`. Open the URL Vite prints. Try refreshing the list, adding a sample user, editing it and deleting it. JSONPlaceholder simulates writes. New entries remain editable in this page until you refresh.

## MongoDB PDF index · slides 38–39

From `09.2-pdf-index`, install `requirements.txt` in a Python environment. Give your local `.env` the Atlas URI and Gemini key from your private lesson setup. Run `python check_atlas.py` first. If the PDF index is missing, run `python exercise_1.py`. Then check that `test-index-1` and `test-index-pdf` are both ready in Atlas or with the checker. This exercise stops at setting up the index.

## Tavily MCP · slides 22–24

Use the folder's requirements and a private `.env` with the Gemini and Tavily keys. Start `python server/http/roll_dice.py` in the first terminal. Run `python main.py` in a second terminal in the same folder. Check that the tools used include Tavily search and `get_number`, and open the returned article to confirm the publication date.

## Books MCP · slides 26–31

Use the folder's requirements and a private `.env` with the Gemini key, Tavily key and `DATABASE_URL` for your lesson database. For a fresh database, run `books.sql` once to seed the two rows. With your existing seeded database, start the dice server in the first terminal and run `python main.py` in a second. Look for `list_tables` and `run_query`. The expected answer is two books, with Diana Ramli as the author of the first row by ID.

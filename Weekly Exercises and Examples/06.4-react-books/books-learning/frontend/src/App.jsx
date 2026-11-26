import { useState } from "react";
import axios from "axios";

function App() {
  const [books, setBooks] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [publishedYear, setPublishedYear] = useState("");

  async function loadBooks() {
    setLoading(true);
    setError("");

    try {
      const response = await axios.get(
        "http://127.0.0.1:8002/books"
      );

      setBooks(response.data);
    } catch {
      setError("Could not load books. Check that FastAPI is running.");
    } finally {
      setLoading(false);
    }
  }

  async function addBook(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await axios.post("http://127.0.0.1:8002/books", {
        title: title,
        author: author,
        published_year: Number(publishedYear),
      });

      setTitle("");
      setAuthor("");
      setPublishedYear("");

      await loadBooks();
    } catch {
      setError("Could not add the book. Check the details and API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>My Book Library</h1>

      <form onSubmit={addBook}>
        <fieldset disabled={loading}>
          <legend>Add a book</legend>

          <label>
            Title
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
              minLength={3}
              maxLength={200}
            />
          </label>

          <label>
            Author
            <input
              value={author}
              onChange={(event) => setAuthor(event.target.value)}
              required
              minLength={3}
              maxLength={100}
            />
          </label>

          <label>
            Published year
            <input
              type="number"
              value={publishedYear}
              onChange={(event) => setPublishedYear(event.target.value)}
              required
              min={1800}
              step={1}
            />
          </label>

          <button type="submit">Add book</button>
        </fieldset>
      </form>

      <button onClick={loadBooks} disabled={loading}>
        {loading ? "Loading..." : "Load books"}
      </button>

      {error && <p role="alert">{error}</p>}

      <ul>
        {books.map((book) => (
          <li key={book.id}>
            #{book.id}: {book.title} — {book.author}
            {" "}({book.published_year})
          </li>
        ))}
      </ul>
    </main>
  );
}

export default App;
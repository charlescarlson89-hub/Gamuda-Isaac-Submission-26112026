import { useCallback, useEffect, useRef, useState } from 'react'
import { createBook, deleteBook, errorMessage, getBooks, updateBook } from '../services/booksApi.js'
import './BookManager.css'

const emptyForm = { title: '', author: '', published_year: '' }

export default function BookManager() {
  const [books, setBooks] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [connected, setConnected] = useState(false)
  const titleInput = useRef(null)
  const requestId = useRef(0)
  const [currentYear] = useState(() => new Date().getFullYear())
  const busy = loading || saving

  // GET: fetch database records when the page opens, or after a change.
  const loadBooks = useCallback((signal) => {
    const id = ++requestId.current
    return getBooks(signal).then((response) => {
      if (id !== requestId.current) return
      setBooks(response.data.toSorted((a, b) => a.id - b.id))
      setConnected(true)
    }).catch((problem) => {
      if (signal?.aborted || id !== requestId.current) return
      setConnected(false)
      setError(errorMessage(problem))
    }).finally(() => {
      if (id === requestId.current && !signal?.aborted) setLoading(false)
    })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    loadBooks(controller.signal)
    return () => controller.abort()
  }, [loadBooks])

  async function refreshBooks() {
    setLoading(true)
    setError('')
    await loadBooks()
  }

  function changeField(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  function resetForm() {
    setEditingId(null)
    setForm(emptyForm)
  }

  function editBook(book) {
    setEditingId(book.id)
    setForm({ title: book.title, author: book.author, published_year: String(book.published_year) })
    setDeleteTarget(null)
    setError('')
    setNotice('')
    titleInput.current?.focus()
  }

  // POST adds a book; PUT updates the selected book using its database ID.
  async function saveBook(event) {
    event.preventDefault()
    if (busy) return
    const payload = {
      title: form.title.trim(),
      author: form.author.trim(),
      published_year: Number(form.published_year),
    }
    if (payload.title.length < 3 || payload.author.length < 3) {
      setError('Title and author must each contain at least 3 characters.')
      return
    }
    if (!Number.isInteger(payload.published_year) || payload.published_year < 1800 || payload.published_year > currentYear) {
      setError(`Enter a whole publication year between 1800 and ${currentYear}.`)
      return
    }
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const response = editingId === null
        ? await createBook(payload)
        : await updateBook(editingId, payload)
      setNotice(`Book #${response.data.id} ${editingId === null ? 'added' : 'updated'} in PostgreSQL.`)
      resetForm()
      await refreshBooks()
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setSaving(false)
    }
  }

  // DELETE only runs after the user confirms the selected record.
  async function confirmDelete() {
    if (!deleteTarget || busy) return
    const book = deleteTarget
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await deleteBook(book.id)
      if (editingId === book.id) resetForm()
      setDeleteTarget(null)
      setNotice(`Book #${book.id} deleted from PostgreSQL.`)
      await refreshBooks()
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="books-app">
      <header className="page-header">
        <div>
          <p className="eyebrow">YOUR PERSONAL LIBRARY</p>
          <h1>A shelf of good stories.</h1>
          <p className="intro">Add a book, find an old favourite, and keep your collection in order.</p>
        </div>
        <span className={`connection ${connected ? 'is-connected' : ''}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {loading ? 'Connecting...' : connected ? 'Books API connected' : 'API unavailable'}
        </span>
      </header>

      {error && <div className="message error" role="alert">{error}</div>}
      {notice && <div className="message success" role="status">{notice}</div>}

      <div className="library-layout">
        <section className="panel form-panel" aria-labelledby="form-heading">
          <p className="eyebrow">{editingId === null ? 'MAKE ROOM FOR ANOTHER' : `BOOK #${editingId}`}</p>
          <h2 id="form-heading">{editingId === null ? 'Add a new book' : 'Edit your book'}</h2>
          <p className="panel-description">{editingId === null ? 'A few details are all you need.' : 'Update the details, then save your changes.'}</p>
          <form onSubmit={saveBook}>
            <fieldset disabled={busy}>
              <label htmlFor="book-title">Book title</label>
              <input ref={titleInput} id="book-title" name="title" value={form.title} onChange={changeField} required minLength={3} maxLength={1000} placeholder="e.g. The Hobbit" />

              <label htmlFor="book-author">Author</label>
              <input id="book-author" name="author" value={form.author} onChange={changeField} required minLength={3} maxLength={1000} placeholder="e.g. J. R. R. Tolkien" />

              <label htmlFor="book-year">Published year</label>
              <input id="book-year" name="published_year" type="number" min={1800} max={currentYear} step={1} value={form.published_year} onChange={changeField} required placeholder="e.g. 1937" />

              <button className="button primary" type="submit">{saving ? 'Saving...' : editingId === null ? 'Add book' : 'Save changes'}</button>
              {editingId !== null && <button className="button secondary cancel-edit" type="button" onClick={resetForm}>Cancel editing</button>}
            </fieldset>
          </form>
          <div className="form-note"><span aria-hidden="true">↳</span> Your collection is saved in PostgreSQL.</div>
        </section>

        <section className="panel collection-panel" aria-labelledby="collection-heading" aria-busy={loading}>
          <div className="collection-header">
            <div><p className="eyebrow">THE COLLECTION</p><h2 id="collection-heading">Your books <span className="book-count">{books.length}</span></h2></div>
            <button className="button secondary" type="button" disabled={busy} onClick={refreshBooks}>Refresh list</button>
          </div>

          {deleteTarget && (
            <div className="delete-confirmation" role="group" aria-label="Delete book confirmation">
              <p>Delete <strong>{deleteTarget.title}</strong> (ID {deleteTarget.id})? This removes it from your database.</p>
              <div className="confirmation-actions">
                <button type="button" className="button danger" disabled={busy} onClick={confirmDelete}>Confirm delete</button>
                <button type="button" className="button secondary" disabled={busy} onClick={() => setDeleteTarget(null)}>Keep book</button>
              </div>
            </div>
          )}

          {loading && <p className="loading" role="status">Loading your books...</p>}
          {!loading && !books.length && (
            <div className="empty-state"><span aria-hidden="true">▤</span><h3>{connected ? 'Your shelf is ready.' : 'Let’s get connected.'}</h3><p>{connected ? 'Add your first book using the form.' : 'Start the Books API, then click Refresh list.'}</p></div>
          )}
          {books.length > 0 && (
            <div className="table-scroll">
              <table>
                <caption className="sr-only">Books saved in your PostgreSQL database</caption>
                <thead><tr><th scope="col">ID</th><th scope="col">Title & author</th><th scope="col">Year</th><th scope="col">Actions</th></tr></thead>
                <tbody>{books.map((book) => (
                  <tr key={book.id} className={editingId === book.id ? 'editing-row' : ''}>
                    <td className="id-cell">#{book.id}</td>
                    <td><span className="book-title">{book.title}</span><span className="book-author">{book.author}</span></td>
                    <td className="year-cell">{book.published_year}</td>
                    <td><div className="row-actions">
                      <button type="button" disabled={busy} aria-label={`Edit book ${book.id}: ${book.title}`} onClick={() => editBook(book)}>Edit</button>
                      <button type="button" className="delete-action" disabled={busy} aria-label={`Delete book ${book.id}: ${book.title}`} onClick={() => { setDeleteTarget(book); setError(''); setNotice('') }}>Delete</button>
                    </div></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
          <p className="collection-note">Each book has its own database ID. Changes are saved as you make them.</p>
        </section>
      </div>
      <footer className="page-footer"><span>BOOKSHELF</span><span>One book at a time.</span></footer>
    </main>
  )
}

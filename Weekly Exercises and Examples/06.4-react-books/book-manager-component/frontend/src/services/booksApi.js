import axios from 'axios'

// React sends HTTP requests here; PostgreSQL credentials stay in the backend.
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 10000,
})

export const getBooks = (signal) => api.get('/books', { signal })
export const createBook = (book) => api.post('/books', book)
export const updateBook = (id, book) => api.put(`/books/${id}`, book)
export const deleteBook = (id) => api.delete(`/books/${id}`)

export function errorMessage(error) {
  if (!error.response) return 'Cannot reach the Books API. Check that FastAPI is running on port 8000, then try again.'
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => `${item.loc?.at(-1) || 'Book'}: ${item.msg}`).join('. ')
  }
  return 'The request could not be completed. Please try again.'
}

import ProductList from '../components/ProductList'
import Counter from '../components/Counter'
import { useSearchParams } from 'react-router-dom'

function ProductsPage() {
  return (
    <div className="app">

      <h1>Product List</h1>

      <ProductList />

      <hr />

      <h1>useState Practice</h1>

      <Counter />

    </div>
  )
}

export default ProductsPage
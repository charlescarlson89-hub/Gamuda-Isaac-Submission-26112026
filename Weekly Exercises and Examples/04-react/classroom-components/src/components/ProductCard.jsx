import { useState } from 'react'

function ProductCard({
  id,
  name = 'Unknown Product',
  price = 0,
  image = '',
  isOnSale = false
}) {
  const [quantity, setQuantity] = useState(0)

  const increment = () => {
    setQuantity(quantity + 1)
  }

  const decrement = () => {
    if (quantity > 0) {
      setQuantity(quantity - 1)
    }
  }

  const reset = () => {
    setQuantity(0)
  }

  return (
    <div className="product-card">

      <img
        src={image}
        alt={name}
        className="product-image"
      />

      <h2>{name}</h2>

      <p>Product ID: {id}</p>

      <p>Price: RM {price}</p>

      <p>
        Status: {isOnSale ? 'On Sale' : 'Regular Price'}
      </p>

      <div className="quantity-section">

        <p className="quantity-label">
          Quantity
        </p>

        <div className="quantity-control">

          <button
            className="quantity-button"
            onClick={decrement}
          >
            -
          </button>

          <span className="quantity-number">
            {quantity}
          </span>

          <button
            className="quantity-button"
            onClick={increment}
          >
            +
          </button>

        </div>

        <button
          className="reset-button"
          onClick={reset}
        >
          Reset
        </button>

      </div>

      <p className="product-total">
        Total: RM {price * quantity}
      </p>

    </div>
  )
}

export default ProductCard
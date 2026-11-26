import ProductCard from './ProductCard'

function ProductList() {
  const products = [
    {
      id: 1,
      name: 'Organic Fertilizer',
      price: 15,
      image: '/product-images/organic-fertilizer.png',
      isOnSale: true
    },
    {
      id: 2,
      name: 'Compost Mix',
      price: 20,
      image: '/product-images/compost-mix.png',
      isOnSale: false
    },
    {
      id: 3,
      name: 'Eco Soil Booster',
      price: 12,
      image: '/product-images/eco-soil-booster.png',
      isOnSale: true
    }
  ]

  return (
    <div className="product-list">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          id={product.id}
          name={product.name}
          price={product.price}
          image={product.image}
          isOnSale={product.isOnSale}
        />
      ))}
    </div>
  )
}

export default ProductList
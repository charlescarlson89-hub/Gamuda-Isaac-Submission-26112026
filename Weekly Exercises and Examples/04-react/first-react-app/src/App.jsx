import JSXExample from './Components/JSXExample'

function App() {
  return (
    <div>
      <JSXExample />
      <JSXExample></JSXExample>

      <header>
        <h1>Welcome to React</h1>
        <p>This is my component</p>
        <p>Current time: {new Date().toLocaleTimeString()}</p>
      </header>
    </div>
  )
}

export default App
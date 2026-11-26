import { useState } from 'react'

function WasteList() {
    const [wasteItem, setWasteItem] = useState([
        {
            id: 1,
            name: 'Banana Peel',
            weight: 0.2
        },
        {
            id: 2,
            name: 'Vegetable Scraps',
            weight: 0.5
        }
    ])

    const addWaste = () => {
        const newWaste = {
            id: Date.now(),
            name: 'Food Waste',
            weight: 1
        }

        setWasteItem([
            ...wasteItem,
            newWaste
        ]
        )
    }

    const removeWaste = (id) => {
        setWasteItem(
            wasteItem.filter((item) => item.id !== id)
        )
    }

    return (
        <div className="waste-list">

            <h2>Food Waste List</h2>

            <button onClick={addWaste}>
                Add Food Waste
            </button>

            {wasteItem.map((item) => (
                <div key={item.id}>

                    <p>
                        {item.name} - {item.weight} kg
                    </p>

                    <button
                        onClick={() => removeWaste(item.id)}
                    >
                        Remove
                    </button>

                </div >
            ))}

        </div>
    )
}

export default WasteList
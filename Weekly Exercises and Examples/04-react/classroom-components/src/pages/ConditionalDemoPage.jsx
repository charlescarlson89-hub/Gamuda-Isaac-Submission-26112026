import { useState } from 'react';

function ConditionalDemoPage() {

    const [showText, setShowText] = useState(false);

    const foodWaste = [
        { id: 1, name: 'Banana Peel', accepted: true },
        { id: 2, name: 'Rice', accepted: true },
        { id: 4, name: 'Plastic Bottle', accepted: false },
        { id: 3, name: 'Vegetable Scraps', accepted: true },
    ]

    const acceptedWaste = foodWaste.filter((waste) => waste.accepted);

    return (
        <div>

            <h1>SoilSync Waste Checker</h1>

            <button onClick={() => setShowText(!showText)}>
                {showText ? 'Hide Waste List' : 'Show Accepted Waste'}
            </button>

            {showText && (
                <div>
                    {acceptedWaste.map((waste) => (

                        <div key={waste.id}>

                            <h3>{waste.name}</h3>

                                {waste.accepted ? (
                                    <p>✅ Accepted</p>
                                ) : (
                                    <p>❌ Not Accepted</p>
                                )}

                            </div>
                ))}
                        </div>
                    )}
                </div>
            )
            }

            export default ConditionalDemoPage;
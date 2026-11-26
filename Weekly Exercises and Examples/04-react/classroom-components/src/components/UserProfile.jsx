import { useState } from 'react'

function UserProfile() {
  const [user, setUser] = useState({
    firstName: '',
    lastName: '',
    email: '',
    age: ''
  })

  const handleChange = (e) => {
    const { name, value } = e.target

    setUser({
      ...user,
      [name]: value
    })
  }

  return (
    <div className="profile-card">
      <h2>User Profile</h2>

      <div className="profile-form">
        <input
          type="text"
          name="firstName"
          placeholder="First Name"
          value={user.firstName}
          onChange={handleChange}
        />

        <input
          type="text"
          name="lastName"
          placeholder="Last Name"
          value={user.lastName}
          onChange={handleChange}
        />

        <input
          type="email"
          name="email"
          placeholder="Email"
          value={user.email}
          onChange={handleChange}
        />

        <input
          type="number"
          name="age"
          placeholder="Age"
          value={user.age}
          onChange={handleChange}
        />
      </div>

      <div className="profile-preview">
        <h3>Profile Preview</h3>

        <p>First Name: {user.firstName}</p>
        <p>Last Name: {user.lastName}</p>
        <p>Email: {user.email}</p>
        <p>Age: {user.age}</p>
      </div>
    </div>
  )
}

export default UserProfile
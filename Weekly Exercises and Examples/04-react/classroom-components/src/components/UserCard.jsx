function UserCard({
  name = "Anonymous",
  age = 0,
  isActive = false
}) {
  return (
    <div className="user-card">
      <h2>{name}</h2>

      <p>Age: {age}</p>

      <p className={`status ${isActive ? 'active' : 'inactive'}`}>
        {isActive ? 'Active' : 'Inactive'}
      </p>
    </div>
  )
}

export default UserCard
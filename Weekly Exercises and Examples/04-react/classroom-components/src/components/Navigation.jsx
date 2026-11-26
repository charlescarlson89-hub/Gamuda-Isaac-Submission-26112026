import { NavLink } from 'react-router-dom'

function Navigation() {
    return (
        <nav className="main-nav">

            <NavLink
                to="/"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Home
            </NavLink>

            <NavLink
                to="/camera"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Camera
            </NavLink>

            <NavLink
                to="/rewards"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Rewards
            </NavLink>

            <NavLink
                to="/fertiliser"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Fertiliser
            </NavLink>

            <NavLink
                to="/products"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Products
            </NavLink>

            <NavLink
                to="/keyboard-demo"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Keyboard Demo
            </NavLink>

            <NavLink
                to="/dynamic-list"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Dynamic List
            </NavLink>

            <NavLink
                to="/contact-form"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Contact Form
            </NavLink>

            <NavLink
                to="/conditional-demo"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Conditional Demo
            </NavLink>

            <NavLink
                to="/login-logout-demo"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Login/Logout Demo
            </NavLink>

            <NavLink
                to="/multi-state-dashboard"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Multi-State Dashboard
            </NavLink>

            <NavLink
                to="/real-time-clock"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Real-Time Clock
            </NavLink>

            <NavLink
                to="/window-tracker"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                Window Tracker
            </NavLink>

            <NavLink
                to="/user-management"
                className={({ isActive }) =>
                    isActive ? 'nav-link active' : 'nav-link'
                }
            >
                User Management
            </NavLink>

        </nav>
    )
}

export default Navigation
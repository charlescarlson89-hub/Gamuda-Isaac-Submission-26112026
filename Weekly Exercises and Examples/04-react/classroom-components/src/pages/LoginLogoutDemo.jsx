import {useState} from 'react';

function LoginLogoutDemo() {

    const [isLoggedIn, setIsLoggedIn] = useState(false);

    return (
        <div>

            <h1>Login/Logout Demo</h1>

            {isLoggedIn ? (

                <div>
                    <h2>Welcome, Carlson!</h2>
                    <p>You are currently logged in.</p>

                    <button onClick={() => setIsLoggedIn(false)}>
                        Logout
                    </button>
                </div>
            ) : (
                <div>
                    <h2>Please Login</h2>
                    <p>You must login to access the dashboard.</p>

                    <button onClick={() => setIsLoggedIn(true)}>
                        Login
                    </button>
                </div>
            )}
        </div>
    );
}

export default LoginLogoutDemo;
import React from "react";
import "../../assets/styles/LoginGate.css";

function LoginGate({
    showLoginGate,
    email,
    password,
    setEmail,
    setPassword,
    handleLogin,
    handleRegister,
}) {
    if (!showLoginGate) {
        return null;
    }

    return (
        <div className="login-gate">

            <div className="login-card">

                <h2>
                    Login required
                </h2>

                <p>
                    You have used your free queries.
                    Please log in to continue using
                    the assistant.
                </p>

                <input
                    type="text"
                    placeholder="Username or Email"
                    value={email}
                    onChange={(e) =>
                        setEmail(e.target.value)
                    }
                />

                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) =>
                        setPassword(e.target.value)
                    }
                />

                <div className="auth-buttons">

                    <button
                        className="login-btn"
                        onClick={handleLogin}
                    >
                        Login
                    </button>

                    <button
                        className="register-btn"
                        onClick={handleRegister}
                    >
                        Register
                    </button>

                </div>

            </div>

        </div>
    );
}

export default LoginGate;
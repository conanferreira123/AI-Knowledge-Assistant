import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRegister } from "../api/api.js";
import "../assets/styles/Register.css";

function Register() {
    const navigate = useNavigate();

    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e) => {
        e.preventDefault();

        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setLoading(true);

        try {
            await apiRegister(
                username,
                email,
                password
            );

            // Registration successful.
            // Go back to the chat where the login popup can be used.
            navigate("/chat");

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="register-page">

            <div className="register-card">

                <h1>Create an account</h1>

                <p className="register-subtitle">
                    Create your StudyBuddy account to continue.
                </p>

                <form onSubmit={handleRegister}>

                    <div className="register-field">
                        <label>Username</label>

                        <input
                            type="text"
                            value={username}
                            onChange={(e) =>
                                setUsername(e.target.value)
                            }
                            placeholder="Enter your username"
                            required
                        />
                    </div>

                    <div className="register-field">
                        <label>Email</label>

                        <input
                            type="email"
                            value={email}
                            onChange={(e) =>
                                setEmail(e.target.value)
                            }
                            placeholder="Enter your email"
                            required
                        />
                    </div>

                    <div className="register-field">
                        <label>Password</label>

                        <input
                            type="password"
                            value={password}
                            onChange={(e) =>
                                setPassword(e.target.value)
                            }
                            placeholder="Create a password"
                            required
                        />
                    </div>

                    <div className="register-field">
                        <label>Confirm password</label>

                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) =>
                                setConfirmPassword(e.target.value)
                            }
                            placeholder="Confirm your password"
                            required
                        />
                    </div>

                    {error && (
                        <p className="register-error">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        className="register-submit"
                        disabled={loading}
                    >
                        {loading ? "Creating account..." : "Register"}
                    </button>

                </form>

                <button
                    className="back-to-login"
                    onClick={() => navigate("/chat")}
                >
                    Already have an account? Login
                </button>

            </div>

        </div>
    );
}

export default Register;
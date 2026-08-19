import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "../components/Landing";
import Chat from "../components/Chat";
import Register from "../components/Register";
import Login from "../components/Login";

function AppRoutes() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
            </Routes>
        </BrowserRouter>
    );
}

export default AppRoutes;
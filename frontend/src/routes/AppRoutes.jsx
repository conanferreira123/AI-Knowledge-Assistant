import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "../components/Landing";
import Chat from "../components/Chat";

function AppRoutes() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/chat" element={<Chat />} />
            </Routes>
        </BrowserRouter>
    );
}

export default AppRoutes;
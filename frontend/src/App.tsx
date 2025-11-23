import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppLayout } from "./components/layout/AppLayout"
import { PrivateRoute } from "./components/PrivateRoute"
import { Dashboard } from "./pages/Dashboard"
import { Library } from "./pages/Library"
import { Login } from "./pages/Login"
import { Register } from "./pages/Register"
import { TestProgress } from "./pages/TestProgress"
import { TestVideoCard } from "./pages/TestVideoCard"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes (without sidebar) */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/test-progress" element={<TestProgress />} />
        <Route path="/test-video-card" element={<TestVideoCard />} />

        {/* Protected routes (with sidebar) */}
        <Route element={<PrivateRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/library" element={<Library />} />
            <Route path="/settings" element={<div>Configurações (Em breve)</div>} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

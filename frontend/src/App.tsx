import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppLayout } from "./components/layout/AppLayout"
import { Dashboard } from "./pages/Dashboard"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/library" element={<div>Biblioteca (Em breve)</div>} />
          <Route path="/settings" element={<div>Configurações (Em breve)</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

import { NavLink, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import ItemDetailPage from "./pages/ItemDetailPage";

function App() {
  return (
    <div className="app">
      <header className="top-bar">
        <span className="top-bar-logo">🛒 CartCompare</span>
      </header>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/item/:type/:id" element={<ItemDetailPage />} />
        </Routes>
      </main>

      <nav className="bottom-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          <span className="nav-icon">🏠</span>
          Best Deals
        </NavLink>
        <NavLink to="/search" className={({ isActive }) => (isActive ? "active" : "")}>
          <span className="nav-icon">🔍</span>
          Search
        </NavLink>
      </nav>
    </div>
  );
}

export default App;

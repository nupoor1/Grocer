import { NavLink, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import ItemDetailPage from "./pages/ItemDetailPage";
import SearchBar from "./components/SearchBar";

function App() {
  return (
    <div className="app">
      <header className="top-bar">
        <div className="top-bar-inner">
          <div className="top-bar-nav">
            <span className="top-bar-logo">Grocer</span>
            <NavLink to="/" end className={({ isActive }) => `top-bar-link ${isActive ? "active" : ""}`}>
              Best Deals
            </NavLink>
          </div>
          <SearchBar />
        </div>
      </header>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/item/:type/:id" element={<ItemDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;

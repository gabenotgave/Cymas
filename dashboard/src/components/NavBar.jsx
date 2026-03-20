import { useState } from "react";
import { Menu } from "lucide-react";

import logo from "../assets/logo.png";


const LINKS = [
  { label: "Overview", href: "#overview" },
  { label: "Charts", href: "#charts" },
  { label: "Raw Data", href: "#raw-data" },
];

function handleNavClick(e, href) {
  e.preventDefault();
  document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
}
// Dark Mode

export default function NavBar({ ssid, lastUpdated, darkMode, setDarkMode}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black w-full">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img
            src={logo}
            alt="LANtern"
            width={130}
          />
        </div>

        <div className="hidden md:flex items-center gap-6">
          {LINKS.map(({ label, href }) => (
            <a
              key={href}
              href={href}
              onClick={(e) => handleNavClick(e, href)}
              className="text-gray-400 hover:text-white text-sm transition-colors"
            >
              {label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
         <button className="text-white" onClick={()=> setDarkMode(!darkMode)}>{darkMode ? "Light Mode" : "Dark Mode"}</button>
          {ssid != null && ssid !== "" && (
            <span className="bg-gray-700 text-gray-300 text-xs rounded-full px-3 py-1">
              {ssid}
            </span>
          )}
          {lastUpdated != null && lastUpdated !== "" && (
            <span className="text-gray-500 text-xs">Last updated {lastUpdated}</span>
          )}
          <button
            type="button"
            className="md:hidden p-1 text-gray-400 hover:text-white"
            onClick={() => setMenuOpen((o) => !o)}
            aria-expanded={menuOpen}
            aria-label="Toggle menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

      </div>
      {menuOpen && (
        <div className="md:hidden bg-gray-900 px-4 pb-3 flex flex-col gap-2">
          {LINKS.map(({ label, href }) => (
            <a
              key={href}
              href={href}
              onClick={(e) => {
                handleNavClick(e, href);
                setMenuOpen(false);
              }}
              className="text-gray-400 hover:text-white text-sm transition-colors py-1"
            >
              {label}
            </a>
          ))}

        </div>
      )}
    </nav>
  );
}

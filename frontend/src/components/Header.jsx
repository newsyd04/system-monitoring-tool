import React, { useState } from "react";

export default function Header() {
    const [isOpen, setIsOpen] = useState(false);
  
    const toggleMenu = () => {
      setIsOpen(!isOpen);
    };
  
  return (
    <nav className="bg-white shadow-md fixed top-0 left-0 w-full z-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <h1 className="text-2xl font-semibold text-gray-800">
            <a href="#home">System Monitoring Tool</a>
          </h1>

          {/* Hamburger Menu Button */}
          <button
            className="block md:hidden text-gray-600 focus:outline-none"
            onClick={toggleMenu}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={isOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
              />
            </svg>
          </button>

          {/* Desktop Menu */}
          <ul className="hidden md:flex space-x-4">
            <li>
              <a href="#selector" className="text-gray-600 hover:text-gray-900">
                Device Selector
              </a>
            </li>
            <li>
              <a href="#metric" className="text-gray-600 hover:text-gray-900">
                Metrics
              </a>
            </li>
            <li>
              <a href="#graph" className="text-gray-600 hover:text-gray-900">
                Graphs
              </a>
            </li>
          </ul>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <ul className="md:hidden flex flex-col space-y-2 pb-4">
            <li>
              <a
                href="#selector"
                className="block text-gray-600 hover:text-gray-900 text-center"
                onClick={toggleMenu}
              >
                Device Selector
              </a>
            </li>
            <li>
              <a
                href="#metric"
                className="block text-gray-600 hover:text-gray-900 text-center"
                onClick={toggleMenu}
              >
                Metrics
              </a>
            </li>
            <li>
              <a
                href="#graph"
                className="block text-gray-600 hover:text-gray-900 text-center"
                onClick={toggleMenu}
              >
                Graphs
              </a>
            </li>
          </ul>
        )}
      </div>
    </nav> 
  );
}

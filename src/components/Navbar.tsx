
import React from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  
  return (
    <nav className="py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b">
      <div className="container-custom flex items-center justify-between">
        <div className="flex items-center">
          <a href="#" className="flex items-center">
            <span className="text-2xl font-bold gradient-text">streamTip</span>
          </a>
        </div>
        
        <div className="hidden md:flex items-center space-x-8">
          <a href="#features" className="font-medium text-gray-700 hover:text-purple transition-colors">Features</a>
          <a href="#how-it-works" className="font-medium text-gray-700 hover:text-purple transition-colors">How It Works</a>
          <a href="#pricing" className="font-medium text-gray-700 hover:text-purple transition-colors">Pricing</a>
          <a href="#faq" className="font-medium text-gray-700 hover:text-purple transition-colors">FAQ</a>
        </div>
        
        <div className="hidden md:flex items-center space-x-4">
          <Button variant="outline">Log in</Button>
          <Button>Get started</Button>
        </div>
        
        <button 
          className="md:hidden text-gray-700" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="h-6 w-6">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
      </div>
      
      {isMenuOpen && (
        <div className="md:hidden absolute top-16 inset-x-0 bg-white shadow-lg rounded-b-lg z-50">
          <div className="flex flex-col p-4 space-y-3">
            <a href="#features" className="py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-md" onClick={() => setIsMenuOpen(false)}>Features</a>
            <a href="#how-it-works" className="py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-md" onClick={() => setIsMenuOpen(false)}>How It Works</a>
            <a href="#pricing" className="py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-md" onClick={() => setIsMenuOpen(false)}>Pricing</a>
            <a href="#faq" className="py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-md" onClick={() => setIsMenuOpen(false)}>FAQ</a>
            <div className="pt-2 flex flex-col space-y-2">
              <Button variant="outline" className="w-full">Log in</Button>
              <Button className="w-full">Get started</Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;

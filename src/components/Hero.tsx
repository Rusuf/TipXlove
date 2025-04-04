
import React from "react";
import { Button } from "@/components/ui/button";

const Hero = () => {
  return (
    <section className="pt-10 pb-20 md:pt-16 md:pb-28 bg-hero-pattern">
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="flex flex-col space-y-8">
            <div>
              <p className="text-purple font-semibold mb-3">A better way to support creators</p>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                Get <span className="gradient-text">rewarded</span> for your creativity
              </h1>
              <p className="mt-6 text-lg text-gray-700 md:text-xl max-w-lg">
                streamTip makes it easy for creators to receive tips from their audience and build a sustainable income through fan support.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button className="btn-gradient text-lg py-6 px-8">
                Start receiving tips
              </Button>
              <Button variant="outline" className="text-lg py-6 px-8">
                See how it works
              </Button>
            </div>

            <div className="pt-4">
              <p className="text-gray-500 text-sm mb-3">Trusted by creators everywhere</p>
              <div className="flex flex-wrap gap-8 items-center">
                <div className="text-gray-400">10,000+ creators</div>
                <div className="text-gray-400">$5M+ paid out</div>
                <div className="text-gray-400">100K+ happy fans</div>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="relative z-10 bg-white rounded-2xl shadow-xl p-6 animate-float">
              <div className="flex items-center space-x-4 mb-6">
                <div className="h-12 w-12 rounded-full bg-purple-light flex items-center justify-center text-white font-bold">
                  JD
                </div>
                <div>
                  <h3 className="font-bold text-lg">Jane's Design Studio</h3>
                  <p className="text-gray-500">Graphic Designer & Illustrator</p>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-xl p-4 mb-6">
                <p className="text-gray-700">Just dropped a new design tutorial! If you found it helpful, consider leaving a tip 💜</p>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <button className="bg-gray-100 hover:bg-gray-200 py-3 px-2 rounded-lg text-center">
                  <div className="font-semibold">$5</div>
                  <div className="text-xs text-gray-500">Coffee</div>
                </button>
                <button className="bg-gray-100 hover:bg-gray-200 py-3 px-2 rounded-lg text-center">
                  <div className="font-semibold">$10</div>
                  <div className="text-xs text-gray-500">Lunch</div>
                </button>
                <button className="bg-purple-light text-white hover:bg-purple py-3 px-2 rounded-lg text-center">
                  <div className="font-semibold">$20</div>
                  <div className="text-xs text-white/80">Support</div>
                </button>
              </div>
              
              <div className="mt-6">
                <button className="btn-gradient w-full py-3 rounded-lg text-white font-medium">
                  Send support to Jane
                </button>
              </div>
            </div>
            
            <div className="absolute top-8 -right-4 bg-white rounded-2xl shadow-xl p-4 z-0 hidden md:block">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center text-white text-sm font-bold">
                  TS
                </div>
                <div className="text-sm">
                  <p className="font-medium">Tom S. sent $20</p>
                  <p className="text-gray-500 text-xs">Great tutorial, thanks!</p>
                </div>
              </div>
            </div>
            
            <div className="absolute -bottom-4 -left-4 bg-white rounded-2xl shadow-xl p-4 z-0 hidden md:block">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-bold">
                  AK
                </div>
                <div className="text-sm">
                  <p className="font-medium">Amy K. sent $10</p>
                  <p className="text-gray-500 text-xs">Keep up the amazing work!</p>
                </div>
              </div>
            </div>
            
            <div className="absolute -z-10 w-full h-full top-0 left-0 bg-gradient-radial from-purple/10 to-transparent rounded-full blur-3xl" />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;

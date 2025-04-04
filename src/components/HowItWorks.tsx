
import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="section">
      <div className="container-custom">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">How <span className="gradient-text">streamTip</span> works</h2>
          <p className="text-lg text-gray-700">
            Our platform makes it simple for creators to receive support and for fans to show their appreciation.
          </p>
        </div>

        <Tabs defaultValue="creators" className="max-w-5xl mx-auto">
          <TabsList className="grid w-full grid-cols-2 mb-12">
            <TabsTrigger value="creators">For Creators</TabsTrigger>
            <TabsTrigger value="fans">For Fans</TabsTrigger>
          </TabsList>
          
          <TabsContent value="creators">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-purple/10 flex items-center justify-center mb-6">
                  <span className="text-purple font-bold text-xl">1</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Create your account</h3>
                <p className="text-gray-600">Sign up in minutes and customize your profile to reflect your brand and style.</p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-purple/10 flex items-center justify-center mb-6">
                  <span className="text-purple font-bold text-xl">2</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Share your tip link</h3>
                <p className="text-gray-600">Add your streamTip link to your social media profiles, website, and content descriptions.</p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-purple/10 flex items-center justify-center mb-6">
                  <span className="text-purple font-bold text-xl">3</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Receive tips & grow</h3>
                <p className="text-gray-600">Get paid directly from your fans and build a sustainable income stream from your creativity.</p>
              </div>
            </div>
            
            <div className="mt-12 rounded-xl overflow-hidden shadow-lg">
              <img 
                src="https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=1200&q=80" 
                alt="Creator dashboard" 
                className="w-full h-auto"
              />
            </div>
          </TabsContent>
          
          <TabsContent value="fans">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-pink/10 flex items-center justify-center mb-6">
                  <span className="text-pink font-bold text-xl">1</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Find your favorite creator</h3>
                <p className="text-gray-600">Visit their streamTip link from their social profiles, website, or content descriptions.</p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-pink/10 flex items-center justify-center mb-6">
                  <span className="text-pink font-bold text-xl">2</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Choose a tip amount</h3>
                <p className="text-gray-600">Select from suggested amounts or enter a custom tip to show your appreciation.</p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 rounded-full bg-pink/10 flex items-center justify-center mb-6">
                  <span className="text-pink font-bold text-xl">3</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">Complete your payment</h3>
                <p className="text-gray-600">Pay securely with credit card, PayPal, or other payment methods in just a few clicks.</p>
              </div>
            </div>
            
            <div className="mt-12 rounded-xl overflow-hidden shadow-lg">
              <img 
                src="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1200&q=80" 
                alt="Fan tipping interface" 
                className="w-full h-auto"
              />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
};

export default HowItWorks;

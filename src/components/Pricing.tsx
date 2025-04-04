
import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

const Pricing = () => {
  const plans = [
    {
      name: "Basic",
      description: "Perfect for creators just starting out",
      price: "Free",
      features: [
        "Custom tipping page",
        "Basic analytics",
        "2.9% + $0.30 per transaction",
        "Standard payouts (3-5 days)",
        "Email support"
      ],
      highlighted: false,
      buttonText: "Get started",
      buttonVariant: "outline"
    },
    {
      name: "Pro",
      description: "For growing creators with an engaged audience",
      price: "$9/mo",
      features: [
        "Everything in Basic",
        "Advanced analytics",
        "1.9% + $0.30 per transaction",
        "Fast payouts (1-2 days)",
        "Custom tip messages",
        "Priority support"
      ],
      highlighted: true,
      buttonText: "Get started",
      buttonVariant: "default"
    },
    {
      name: "Business",
      description: "For established creators and teams",
      price: "$29/mo",
      features: [
        "Everything in Pro",
        "Multiple team members",
        "1.5% + $0.30 per transaction",
        "Instant payouts",
        "White-label experience",
        "VIP support"
      ],
      highlighted: false,
      buttonText: "Get started",
      buttonVariant: "outline"
    }
  ];

  return (
    <section id="pricing" className="section">
      <div className="container-custom">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Simple, <span className="gradient-text">transparent</span> pricing</h2>
          <p className="text-lg text-gray-700">
            Choose the plan that's right for your creator journey, with no hidden fees or surprises.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <Card 
              key={index} 
              className={`card-hover relative ${
                plan.highlighted ? "border-purple shadow-glow" : ""
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-0 right-0 flex justify-center">
                  <span className="bg-gradient-to-r from-purple to-pink text-white px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}
              
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              
              <CardContent>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.price !== "Free" && <span className="text-gray-500 ml-1">USD</span>}
                </div>
                
                <ul className="space-y-3">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start">
                      <Check className="h-5 w-5 text-purple mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              
              <CardFooter>
                <Button 
                  className={`w-full ${plan.highlighted ? "btn-gradient" : ""}`} 
                  variant={plan.highlighted ? "default" : "outline" as any}
                >
                  {plan.buttonText}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
        
        <div className="mt-12 text-center">
          <p className="text-gray-500">
            All plans include secure payment processing, streamTip's creator dashboard, and unlimited tips.
          </p>
        </div>
      </div>
    </section>
  );
};

export default Pricing;


import React from "react";
import { Button } from "@/components/ui/button";

const Cta = () => {
  return (
    <section className="py-24 bg-gradient-to-r from-purple to-pink">
      <div className="container-custom text-center">
        <div className="max-w-3xl mx-auto text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to turn your passion into income?
          </h2>
          <p className="text-lg mb-8 text-white/90">
            Join thousands of creators already using streamTip to connect with their audience and build a sustainable income stream.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-white text-purple hover:bg-white/90" variant="outline">
              Create your free account
            </Button>
            <Button size="lg" className="bg-transparent border-2 border-white text-white hover:bg-white/10" variant="outline">
              Learn more
            </Button>
          </div>
          <p className="mt-6 text-sm text-white/70">
            No credit card required. Get started in minutes.
          </p>
        </div>
      </div>
    </section>
  );
};

export default Cta;

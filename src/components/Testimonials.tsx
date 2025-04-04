
import React from "react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";

const Testimonials = () => {
  const testimonials = [
    {
      name: "Alex Rivera",
      role: "Music Producer",
      content: "streamTip has changed how I connect with my fans. I can now focus on creating music full-time thanks to the consistent support I receive through the platform.",
      avatar: "AR",
      avatarColor: "bg-blue-500",
    },
    {
      name: "Sarah Chen",
      role: "Digital Artist",
      content: "I was skeptical at first, but streamTip has become my primary income source. The ease of setting up and sharing my page has helped me grow my community exponentially.",
      avatar: "SC",
      avatarColor: "bg-purple-dark",
    },
    {
      name: "Marcus Johnson",
      role: "Podcast Host",
      content: "My listeners wanted a simple way to support the show. With streamTip, they can contribute in seconds, and I can easily thank them and recognize their support.",
      avatar: "MJ",
      avatarColor: "bg-green-500",
    },
    {
      name: "Priya Sharma",
      role: "Food Blogger",
      content: "The analytics dashboard helps me understand which content resonates most with my audience. This insight has been invaluable for growing my food blog.",
      avatar: "PS",
      avatarColor: "bg-pink",
    },
  ];

  return (
    <section className="section bg-gray-50">
      <div className="container-custom">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Loved by <span className="gradient-text">creators worldwide</span></h2>
          <p className="text-lg text-gray-700">
            Thousands of creators rely on streamTip to connect with their audience and receive support for their work.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="card-hover">
              <CardContent className="pt-6">
                <div className="flex mb-6">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                
                <p className="text-gray-700 mb-4">&ldquo;{testimonial.content}&rdquo;</p>
              </CardContent>
              
              <CardFooter className="pt-0">
                <div className="flex items-center">
                  <div className={`h-10 w-10 rounded-full ${testimonial.avatarColor} flex items-center justify-center text-white font-bold mr-3`}>
                    {testimonial.avatar}
                  </div>
                  <div>
                    <h4 className="font-semibold">{testimonial.name}</h4>
                    <p className="text-sm text-gray-500">{testimonial.role}</p>
                  </div>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
        
        <div className="flex justify-center mt-12">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-2xl text-center">
            <div className="text-3xl font-bold mb-4">
              <span className="text-purple">94%</span> of creators report increased income
            </div>
            <p className="text-gray-700">
              Join thousands of creators who have transformed their passion into a sustainable income stream through streamTip.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Testimonials;


import React from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const Faq = () => {
  const faqs = [
    {
      question: "How quickly can I withdraw my tips?",
      answer: "Withdrawal times depend on your plan. Basic users can withdraw funds within 3-5 business days, Pro users within 1-2 business days, and Business users can access instant withdrawals. All withdrawals are subject to our standard fraud prevention checks."
    },
    {
      question: "What payment methods do you support?",
      answer: "We support major credit and debit cards, PayPal, Apple Pay, Google Pay, and bank transfers in supported countries. The available payment methods may vary depending on your location."
    },
    {
      question: "Can I customize my tipping page?",
      answer: "Absolutely! All plans include customization options for your tipping page, including colors, images, and messaging. Pro and Business plans offer more extensive customization options, including custom domains and branding removal."
    },
    {
      question: "Is there a minimum tip amount?",
      answer: "The minimum tip amount is $1 USD or equivalent in your local currency. You can suggest higher tip amounts to your audience, but we keep the minimum low so fans can contribute what they can."
    },
    {
      question: "Which countries are supported?",
      answer: "streamTip is available in over 40 countries worldwide. Our payment processing and payouts are supported in major markets including the US, Canada, EU countries, UK, Australia, and many more. Contact support for specific country availability."
    },
    {
      question: "Can I offer rewards to my fans for tipping?",
      answer: "Yes! You can create custom thank-you messages for different tip amounts. Pro and Business plans also include the ability to offer digital rewards, exclusive content access, and other perks to your supporters."
    }
  ];

  return (
    <section id="faq" className="section bg-gray-50">
      <div className="container-custom">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Frequently <span className="gradient-text">Asked</span> Questions</h2>
          <p className="text-lg text-gray-700">
            Everything you need to know about streamTip and how it works.
          </p>
        </div>
        
        <div className="max-w-3xl mx-auto">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left text-lg font-medium">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-gray-700">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
        
        <div className="mt-12 text-center">
          <p className="text-gray-700 mb-4">Still have questions?</p>
          <a href="#" className="text-purple hover:text-purple-dark font-medium">
            Contact our support team →
          </a>
        </div>
      </div>
    </section>
  );
};

export default Faq;

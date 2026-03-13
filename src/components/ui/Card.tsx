import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
}

const Card = ({ children, className = '', title }: CardProps) => (
  <div className={`bg-white rounded-xl shadow-lg border border-gray-200 p-6 hover:shadow-xl transition-all duration-200 ${className}`}>
    {title && (
      <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b border-green-100 pb-2">
        {title}
      </h2>
    )}
    {children}
  </div>
);

export default Card;

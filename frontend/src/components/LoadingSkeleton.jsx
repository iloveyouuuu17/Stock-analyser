import React from 'react';

export default function LoadingSkeleton() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-pulse">
      {/* Top Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Price Skeleton */}
        <div className="h-32 bg-[#121212] border border-gray-800 rounded-md p-6 flex flex-col justify-center space-y-3">
          <div className="h-4 bg-gray-800 rounded w-1/4"></div>
          <div className="h-10 bg-gray-800 rounded w-1/2"></div>
        </div>
        
        {/* Verdict Skeleton */}
        <div className="h-32 bg-[#121212] border border-gray-800 rounded-md p-6 flex flex-col justify-center space-y-3">
           <div className="h-4 bg-gray-800 rounded w-1/4"></div>
           <div className="h-10 bg-gray-800 rounded w-1/3"></div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Charts */}
        <div className="lg:col-span-1 space-y-6">
          <div className="h-64 bg-[#121212] border border-gray-800 rounded-md p-6 flex justify-center items-center">
            <div className="h-32 w-32 rounded-full bg-gray-800"></div>
          </div>
          <div className="h-64 bg-[#121212] border border-gray-800 rounded-md p-6 relative">
             <div className="absolute bottom-4 left-4 right-4 h-1/2 bg-gray-800/50 rounded-md"></div>
          </div>
        </div>

        {/* Right Col: News Feed */}
        <div className="lg:col-span-2 space-y-3 bg-[#121212] border border-gray-800 rounded-md p-6">
          <div className="h-4 bg-gray-800 rounded w-1/5 mb-6"></div>
          {[...Array(6)].map((_, i) => (
             <div key={i} className="flex gap-4">
               <div className="h-4 bg-gray-800 rounded w-16 shrink-0"></div>
               <div className="h-4 bg-gray-800 rounded w-full"></div>
             </div>
          ))}
        </div>
      </div>
    </div>
  );
}

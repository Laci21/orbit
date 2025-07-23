import React from 'react';
import { Clock } from 'lucide-react';
import { CrisisEvent } from '../data/mockData';

interface TimelineProps {
  events: CrisisEvent[];
  currentStep: number;
}

export const Timeline: React.FC<TimelineProps> = ({ events, currentStep }) => {
  return (
    <div className="bg-gray-900 border border-cyan-500 rounded-lg p-4">
      <div className="flex items-center mb-4">
        <Clock className="w-4 h-4 text-cyan-400 mr-2" />
        <h3 className="text-cyan-400 font-mono text-sm font-bold tracking-wider">
          MISSION TIMELINE
        </h3>
      </div>
      
      <div className="space-y-3">
        {events.slice(0, currentStep + 1).map((event, index) => (
          <div 
            key={event.id}
            className={`flex items-start space-x-3 ${
              index === currentStep ? 'animate-pulse' : ''
            }`}
          >
            <div className={`w-3 h-3 rounded-full mt-1 ${
              event.severity === 'critical' ? 'bg-red-400' :
              event.severity === 'high' ? 'bg-orange-400' :
              event.severity === 'medium' ? 'bg-yellow-400' :
              'bg-green-400'
            }`}></div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-white font-mono text-xs font-bold">
                  {event.title}
                </span>
                <span className="text-gray-500 font-mono text-xs">
                  {event.timestamp}
                </span>
              </div>
              <p className="text-gray-400 text-xs mt-1">
                {event.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
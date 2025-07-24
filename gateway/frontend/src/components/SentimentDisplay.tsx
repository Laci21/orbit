import React from 'react';
import { TrendingDown } from 'lucide-react';

interface SentimentDisplayProps {
  isActive: boolean;
  sentimentData: any;
}

export const SentimentDisplay: React.FC<SentimentDisplayProps> = ({ isActive, sentimentData }) => {
  if (!isActive) {
    return (
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-4 h-full">
        <div className="flex items-center mb-4">
          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
          <h3 className="text-gray-500 font-mono text-sm font-bold tracking-wider">
            SENTIMENT ANALYSIS
          </h3>
        </div>
        <div className="text-center text-gray-600 text-sm">
          Awaiting data...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-orange-500 rounded-lg p-4 h-full">
      <div className="flex items-center mb-4">
        <TrendingDown className="w-4 h-4 text-orange-400 mr-2" />
        <h3 className="text-orange-400 font-mono text-sm font-bold tracking-wider">
          SENTIMENT ANALYSIS
        </h3>
      </div>
      
      <div className="space-y-4">
        {/* Overall Sentiment */}
        <div className="bg-red-900/30 border border-red-700 rounded p-3">
          <div className="text-red-400 font-mono text-xs mb-1">OVERALL SENTIMENT</div>
          <div className="text-red-300 font-bold text-lg">{sentimentData.overall}</div>
          <div className="text-red-400 text-sm">Score: {sentimentData.score}</div>
        </div>
        
        {/* Sentiment Breakdown */}
        <div className="space-y-2">
          <div className="text-cyan-400 font-mono text-xs font-bold">EMOTION BREAKDOWN</div>
          {Object.entries(sentimentData.breakdown).map(([emotion, percentage]) => (
            <div key={emotion} className="flex items-center justify-between">
              <span className="text-white text-sm capitalize">{emotion}</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      emotion === 'anger' ? 'bg-red-500' :
                      emotion === 'disappointment' ? 'bg-orange-500' :
                      emotion === 'concern' ? 'bg-yellow-500' :
                      'bg-gray-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
                <span className="text-gray-400 text-xs w-8">{percentage}%</span>
              </div>
            </div>
          ))}
        </div>
        
        {/* Trending Terms */}
        <div>
          <div className="text-cyan-400 font-mono text-xs font-bold mb-2">TRENDING TERMS</div>
          <div className="flex flex-wrap gap-2">
            {sentimentData.trendingTerms.map((term: string, index: number) => (
              <span 
                key={term}
                className={`px-2 py-1 rounded text-xs font-mono ${
                  index < 2 ? 'bg-red-900/50 text-red-300 border border-red-700' :
                  index < 4 ? 'bg-orange-900/50 text-orange-300 border border-orange-700' :
                  'bg-yellow-900/50 text-yellow-300 border border-yellow-700'
                }`}
              >
                #{term}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
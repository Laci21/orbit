import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

interface SentimentDisplayProps {
  isActive: boolean;
  sentimentData: any;
  liveData?: any;
}

export const SentimentDisplay: React.FC<SentimentDisplayProps> = ({ isActive, sentimentData, liveData }) => {
  // Transform live data to match UI expectations, otherwise use mock data
  const displayData = liveData ? {
    overall: liveData.reputational_risk || 'Unknown',
    score: liveData.overall_sentiment || 0,
    breakdown: {
      anger: Math.round(liveData.sentiment_distribution?.negative * 100) || 0,
      disappointment: Math.round(liveData.sentiment_distribution?.negative * 50) || 0,
      concern: Math.round(liveData.sentiment_distribution?.neutral * 100) || 0,
      neutral: Math.round(liveData.sentiment_distribution?.positive * 100) || 0
    },
    trendingTerms: liveData.key_emotions || []
  } : sentimentData;

  const getSentimentIcon = (score: number) => {
    if (score > 0.1) return <TrendingUp className="w-5 h-5 text-green-400" />;
    if (score < -0.1) return <TrendingDown className="w-5 h-5 text-red-400" />;
    return <Minus className="w-5 h-5 text-yellow-400" />;
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.1) return 'text-green-400';
    if (score < -0.1) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.5) return 'Very Positive';
    if (score > 0.1) return 'Positive';
    if (score > -0.1) return 'Neutral';
    if (score > -0.5) return 'Negative';
    return 'Very Negative';
  };
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
    <div className="bg-gray-900 border-2 border-orange-500 rounded-xl p-5 h-full shadow-lg shadow-orange-500/20">
      <div className="flex items-center mb-5">
        {getSentimentIcon(displayData.score)}
        <h3 className="text-orange-400 font-mono text-lg font-bold tracking-wider ml-2">
          SENTIMENT ANALYSIS
        </h3>
      </div>
      
      <div className="space-y-5">
        {/* Sentiment Gauge */}
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-3">
            {/* Circular gauge background */}
            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#374151"
                strokeWidth="2"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={displayData.score > 0 ? "#10b981" : displayData.score < 0 ? "#ef4444" : "#eab308"}
                strokeWidth="2"
                strokeDasharray={`${Math.abs(displayData.score) * 50}, 100`}
                className="transition-all duration-1000"
              />
            </svg>
            {/* Center content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className={`font-mono text-lg font-bold ${getSentimentColor(displayData.score)}`}>
                {(displayData.score * 100).toFixed(0)}
              </div>
              <div className="text-xs text-gray-400">SCORE</div>
            </div>
          </div>
          
          <div className={`font-mono text-sm font-bold ${getSentimentColor(displayData.score)} mb-1`}>
            {getSentimentLabel(displayData.score)}
          </div>
          <div className="text-gray-400 text-xs">
            Risk Level: {displayData.overall}
          </div>
        </div>
        
        {/* Emotion Breakdown */}
        <div>
          <div className="text-cyan-400 font-mono text-xs font-bold mb-3 tracking-wider">EMOTION BREAKDOWN</div>
          <div className="grid grid-cols-2 gap-2">
            {displayData.breakdown && Object.entries(displayData.breakdown).map(([emotion, percentage]) => (
              <div key={emotion} className="bg-gray-800/50 rounded-lg p-2 border border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white text-xs capitalize font-medium">{emotion}</span>
                  <span className="text-gray-400 text-xs">{percentage as number}%</span>
                </div>
                <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ${
                      emotion === 'anger' ? 'bg-red-500' :
                      emotion === 'disappointment' ? 'bg-orange-500' :
                      emotion === 'concern' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`}
                    style={{ width: `${percentage as number}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Trending Terms */}
        <div>
          <div className="text-cyan-400 font-mono text-xs font-bold mb-3 tracking-wider">KEY EMOTIONS</div>
          <div className="flex flex-wrap gap-2">
            {displayData.trendingTerms && displayData.trendingTerms.map((term: string, index: number) => (
              <span 
                key={term}
                className={`px-2 py-1 rounded-full text-xs font-mono transition-all duration-300 hover:scale-105 ${
                  index < 2 ? 'bg-red-900/50 text-red-300 border border-red-600/50' :
                  index < 4 ? 'bg-orange-900/50 text-orange-300 border border-orange-600/50' :
                  'bg-yellow-900/50 text-yellow-300 border border-yellow-600/50'
                }`}
              >
                {term}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
import React from 'react';
import { AlertTriangle, Play } from 'lucide-react';

interface CrisisAlertProps {
  isActive: boolean;
  tweetData: any;
}

export const CrisisAlert: React.FC<CrisisAlertProps> = ({ isActive, tweetData }) => {
  if (!isActive) {
    return (
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-6 h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <p className="text-green-400 font-mono text-sm">ALL SYSTEMS NOMINAL</p>
          <p className="text-gray-500 text-xs mt-1">Monitoring social channels...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 h-full animate-pulse-border">
      <div className="flex items-center mb-4">
        <AlertTriangle className="w-6 h-6 text-red-400 mr-2 animate-pulse" />
        <h3 className="text-red-400 font-mono text-lg font-bold tracking-wider">
          CRISIS DETECTED
        </h3>
      </div>
      
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
            SR
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-white font-bold text-sm">{tweetData.handle}</span>
              <span className="text-gray-400 text-sm">{tweetData.author}</span>
              <span className="text-blue-400 text-sm">✓</span>
              <span className="text-gray-500 text-xs">•</span>
              <span className="text-gray-500 text-xs">{tweetData.timestamp}</span>
            </div>
            
            <p className="text-white text-sm mb-3 leading-relaxed">
              {tweetData.content}
            </p>
            
            {/* Mock Video Thumbnail */}
            <div className="relative bg-black rounded-lg overflow-hidden mb-3">
              <img 
                src={tweetData.videoThumbnail} 
                alt="Video thumbnail" 
                className="w-full h-64 object-cover"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center shadow-lg">
                  <Play className="w-8 h-8 text-white ml-1" fill="white" />
                </div>
              </div>
              <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                {tweetData.videoDuration}
              </div>
            </div>
            
            <div className="text-gray-400 text-xs mb-3">
              Last edited 4:05 PM • {tweetData.views}
            </div>
            
            <div className="flex items-center space-x-6 text-gray-400 text-sm">
              <span className="flex items-center space-x-1">
                <span>💬</span>
                <span>{tweetData.replies}</span>
              </span>
              <span className="flex items-center space-x-1">
                <span>🔄</span>
                <span>{tweetData.retweets}</span>
              </span>
              <span className="flex items-center space-x-1">
                <span>❤️</span>
                <span>{tweetData.likes}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
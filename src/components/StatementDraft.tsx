import React from 'react';
import { Send, CheckCircle } from 'lucide-react';

interface StatementDraftProps {
  isActive: boolean;
  isPublished: boolean;
  draftContent: string;
  onApprove: () => void;
}

export const StatementDraft: React.FC<StatementDraftProps> = ({ 
  isActive, 
  isPublished, 
  draftContent, 
  onApprove 
}) => {
  if (!isActive && !isPublished) {
    return (
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-4 h-full">
        <div className="flex items-center mb-4">
          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
          <h3 className="text-gray-500 font-mono text-sm font-bold tracking-wider">
            STATEMENT GENERATOR
          </h3>
        </div>
        <div className="text-center text-gray-600 text-sm">
          Awaiting agent input...
        </div>
      </div>
    );
  }

  if (isPublished) {
    return (
      <div className="bg-green-900/20 border border-green-500 rounded-lg p-4 h-full">
        <div className="flex items-center mb-4">
          <CheckCircle className="w-4 h-4 text-green-400 mr-2" />
          <h3 className="text-green-400 font-mono text-sm font-bold tracking-wider">
            STATEMENT PUBLISHED
          </h3>
        </div>
        
        <div className="bg-green-900/30 border border-green-700 rounded p-3 mb-4">
          <div className="text-green-300 text-sm leading-relaxed">
            {draftContent}
          </div>
        </div>
        
        <div className="text-center">
          <div className="inline-flex items-center space-x-2 text-green-400 text-sm">
            <CheckCircle className="w-4 h-4" />
            <span className="font-mono">TRANSMISSION COMPLETE</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-purple-500 rounded-lg p-4 h-full">
      <div className="flex items-center mb-4">
        <Send className="w-4 h-4 text-purple-400 mr-2" />
        <h3 className="text-purple-400 font-mono text-sm font-bold tracking-wider">
          DRAFT STATEMENT
        </h3>
      </div>
      
      <div className="bg-purple-900/20 border border-purple-700 rounded p-3 mb-4">
        <div className="text-gray-300 text-sm leading-relaxed">
          {draftContent}
        </div>
      </div>
      
      <div className="text-center">
        <button
          onClick={onApprove}
          className="bg-purple-600 hover:bg-purple-500 text-white font-mono text-sm px-6 py-2 rounded-lg border border-purple-400 transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/20 transform hover:scale-105"
        >
          APPROVE & PUBLISH
        </button>
      </div>
    </div>
  );
};
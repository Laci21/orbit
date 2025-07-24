import React from 'react';
import { FileText } from 'lucide-react';

interface PolicyPanelProps {
  isActive: boolean;
  policyData: any;
}

export const PolicyPanel: React.FC<PolicyPanelProps> = ({ isActive, policyData }) => {
  if (!isActive) {
    return (
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-4 h-full">
        <div className="flex items-center mb-4">
          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
          <h3 className="text-gray-500 font-mono text-sm font-bold tracking-wider">
            POLICY DATABASE
          </h3>
        </div>
        <div className="text-center text-gray-600 text-sm">
          Standby for retrieval...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-blue-500 rounded-lg p-4 h-full">
      <div className="flex items-center mb-4">
        <FileText className="w-4 h-4 text-blue-400 mr-2" />
        <h3 className="text-blue-400 font-mono text-sm font-bold tracking-wider">
          POLICY RETRIEVED
        </h3>
      </div>
      
      <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
        <div className="text-blue-300 font-mono text-xs font-bold mb-2">
          {policyData.title}
        </div>
        <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-line font-mono">
          {policyData.content}
        </div>
      </div>
    </div>
  );
};
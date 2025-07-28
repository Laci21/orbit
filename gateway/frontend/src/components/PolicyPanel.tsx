import React from 'react';
import { FileText } from 'lucide-react';

interface PolicyPanelProps {
  isActive: boolean;
  policyData: any;
  factData?: any;
  legalData?: any;
  riskData?: any;
}

export const PolicyPanel: React.FC<PolicyPanelProps> = ({ isActive, policyData, factData, legalData, riskData }) => {
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
      
      <div className="space-y-3">
        {/* Policy Information */}
        <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
          <div className="text-blue-300 font-mono text-xs font-bold mb-2">
            {policyData.title}
          </div>
          <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-line font-mono">
            {policyData.content}
          </div>
        </div>

        {/* Fact Check Results */}
        {factData && (
          <div className="bg-green-900/20 border border-green-700 rounded p-3">
            <div className="text-green-300 font-mono text-xs font-bold mb-2">
              FACT CHECK RESULTS
            </div>
            <div className="text-gray-300 text-sm">
              Credibility: {factData.overall_credibility || 'Analyzing...'}
            </div>
            <div className="text-gray-300 text-sm mt-1">
              Claims: {factData.claims_verified || 0} verified, {factData.claims_disputed || 0} disputed
            </div>
            {factData.risk_factors && factData.risk_factors.length > 0 && (
              <div className="text-orange-300 text-xs mt-1">
                Risk: {factData.risk_factors.slice(0, 2).join(', ')}
              </div>
            )}
          </div>
        )}

        {/* Risk Assessment */}
        {riskData && (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3">
            <div className="text-yellow-300 font-mono text-xs font-bold mb-2">
              RISK ASSESSMENT
            </div>
            <div className="text-gray-300 text-sm">
              Level: {riskData.overall_risk_level || 'Analyzing...'}
            </div>
            {riskData.confidence && (
              <div className="text-gray-300 text-sm mt-1">
                Confidence: {Math.round(riskData.confidence * 100)}%
              </div>
            )}
          </div>
        )}

        {/* Legal Review */}
        {legalData && (
          <div className="bg-purple-900/20 border border-purple-700 rounded p-3">
            <div className="text-purple-300 font-mono text-xs font-bold mb-2">
              LEGAL REVIEW
            </div>
            <div className="text-gray-300 text-sm">
              Compliance: {legalData.legal_compliance ? '✅ Compliant' : '❌ Issues Found'}
            </div>
            {legalData.legal_advice && (
              <div className="text-gray-300 text-sm mt-1">
                {legalData.legal_advice}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
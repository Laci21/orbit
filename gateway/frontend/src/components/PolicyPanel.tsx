import React, { useState } from 'react';
import { FileText, Shield, AlertTriangle, Scale, TrendingUp } from 'lucide-react';

interface PolicyPanelProps {
  isActive: boolean;
  policyData: any;
  factData?: any;
  legalData?: any;
  riskData?: any;
}

export const PolicyPanel: React.FC<PolicyPanelProps> = ({ isActive, policyData, factData, legalData, riskData }) => {
  const [activeTab, setActiveTab] = useState<'policy' | 'facts' | 'risk' | 'legal'>('policy');

  const tabs = [
    { id: 'policy' as const, label: 'Policy', icon: FileText, data: policyData },
    { id: 'facts' as const, label: 'Facts', icon: Shield, data: factData },
    { id: 'risk' as const, label: 'Risk', icon: TrendingUp, data: riskData },
    { id: 'legal' as const, label: 'Legal', icon: Scale, data: legalData },
  ];

  if (!isActive) {
    return (
      <div className="bg-gray-900 border-2 border-gray-600 rounded-xl p-5 h-full">
        <div className="flex items-center mb-4">
          <div className="w-3 h-3 bg-gray-600 rounded-full mr-3"></div>
          <h3 className="text-gray-500 font-mono text-lg font-bold tracking-wider">
            ANALYSIS CENTER
          </h3>
        </div>
        <div className="text-center text-gray-600 text-sm">
          Standby for data retrieval...
        </div>
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'policy':
        return (
          <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
            <div className="text-blue-300 font-mono text-sm font-bold mb-3">
              {policyData.title}
            </div>
            <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
              {policyData.content}
            </div>
          </div>
        );
      
      case 'facts':
        return factData ? (
          <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-green-300 font-mono text-sm font-bold">CREDIBILITY ASSESSMENT</div>
              <div className={`px-2 py-1 rounded text-xs font-bold ${
                factData.overall_credibility === 'high' ? 'bg-green-600 text-white' :
                factData.overall_credibility === 'medium' ? 'bg-yellow-600 text-white' :
                'bg-red-600 text-white'
              }`}>
                {factData.overall_credibility?.toUpperCase() || 'ANALYZING'}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="text-center p-2 bg-gray-800/50 rounded border border-gray-700">
                <div className="text-green-400 text-lg font-bold">{factData.claims_verified || 0}</div>
                <div className="text-xs text-gray-400">Verified</div>
              </div>
              <div className="text-center p-2 bg-gray-800/50 rounded border border-gray-700">
                <div className="text-red-400 text-lg font-bold">{factData.claims_disputed || 0}</div>
                <div className="text-xs text-gray-400">Disputed</div>
              </div>
            </div>
            {factData.risk_factors && factData.risk_factors.length > 0 && (
              <div>
                <div className="text-orange-300 font-mono text-xs font-bold mb-2">RISK FACTORS</div>
                <div className="space-y-1">
                  {factData.risk_factors.slice(0, 3).map((factor: string, index: number) => (
                    <div key={index} className="text-gray-300 text-xs flex items-center">
                      <AlertTriangle className="w-3 h-3 text-orange-400 mr-2 flex-shrink-0" />
                      {factor}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">No fact check data available</div>
          </div>
        );
      
      case 'risk':
        return riskData ? (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div className="text-yellow-300 font-mono text-sm font-bold mb-3">RISK ASSESSMENT</div>
            <div className="text-center mb-4">
              <div className={`inline-block px-4 py-2 rounded-lg font-bold text-lg ${
                riskData.overall_risk_level === 'low' ? 'bg-green-600 text-white' :
                riskData.overall_risk_level === 'medium' ? 'bg-yellow-600 text-black' :
                riskData.overall_risk_level === 'high' ? 'bg-orange-600 text-white' :
                'bg-red-600 text-white'
              }`}>
                {riskData.overall_risk_level?.toUpperCase() || 'ANALYZING'}
              </div>
            </div>
            {riskData.confidence && (
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-300 text-sm">Confidence Level</span>
                  <span className="text-yellow-400 font-bold">{Math.round(riskData.confidence * 100)}%</span>
                </div>
                <div className="w-full h-2 bg-gray-700 rounded-full">
                  <div 
                    className="h-2 bg-yellow-400 rounded-full transition-all duration-1000"
                    style={{ width: `${riskData.confidence * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">No risk assessment data available</div>
          </div>
        );
      
      case 'legal':
        return legalData ? (
          <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-4">
            <div className="text-purple-300 font-mono text-sm font-bold mb-3">LEGAL COMPLIANCE</div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-300">Compliance Status</span>
              <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                legalData.legal_compliance ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
              }`}>
                {legalData.legal_compliance ? '✅ COMPLIANT' : '❌ ISSUES FOUND'}
              </div>
            </div>
            {legalData.legal_advice && (
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                <div className="text-purple-300 font-mono text-xs font-bold mb-2">LEGAL ADVICE</div>
                <div className="text-gray-300 text-sm leading-relaxed">
                  {legalData.legal_advice}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">No legal review data available</div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-900 border-2 border-blue-500 rounded-xl p-5 h-full shadow-lg shadow-blue-500/20">
      <div className="flex items-center mb-5">
        <FileText className="w-5 h-5 text-blue-400 mr-3" />
        <h3 className="text-blue-400 font-mono text-lg font-bold tracking-wider">
          ANALYSIS CENTER
        </h3>
      </div>
      
      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 bg-gray-800/50 rounded-lg p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const hasData = tab.data && (tab.id === 'policy' || Object.keys(tab.data).length > 0);
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center px-3 py-2 rounded-md text-xs font-mono font-bold transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-lg'
                  : hasData
                  ? 'text-blue-300 hover:bg-gray-700'
                  : 'text-gray-500 cursor-not-allowed'
              }`}
              disabled={!hasData}
            >
              <Icon className="w-3 h-3 mr-1" />
              {tab.label}
              {hasData && activeTab !== tab.id && (
                <div className="w-2 h-2 bg-green-400 rounded-full ml-1"></div>
              )}
            </button>
          );
        })}
      </div>
      
      {/* Tab Content */}
      <div className="flex-1">
        {renderTabContent()}
      </div>
    </div>
  );
};
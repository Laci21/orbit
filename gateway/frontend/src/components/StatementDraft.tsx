import React from 'react';
import { Send, CheckCircle, Shield, AlertTriangle } from 'lucide-react';

interface PressSecretaryResponse {
  primary_statement: string;
  tone: string;
  key_messages: string[];
  channels: {
    press_release: string;
    social_media: string;
    employee_memo: string;
  };
  legal_compliance: boolean;
  confidence: number;
  reputational_risk?: string;
}

interface StatementDraftProps {
  isActive: boolean;
  isPublished: boolean;
  draftContent: string;
  finalResponse?: { press_secretary_response?: PressSecretaryResponse };
  onApprove: () => void;
}

export const StatementDraft: React.FC<StatementDraftProps> = ({ 
  isActive, 
  isPublished, 
  draftContent,
  finalResponse,
  onApprove 
}) => {
  const pressResponse = finalResponse?.press_secretary_response;
  
  // Debug logging
  React.useEffect(() => {
    if (finalResponse) {
      console.log('StatementDraft received finalResponse:', finalResponse);
      console.log('finalResponse keys:', Object.keys(finalResponse));
      console.log('finalResponse.press_secretary_response:', finalResponse.press_secretary_response);
      console.log('All finalResponse properties:', JSON.stringify(finalResponse, null, 2));
      console.log('Press Secretary Response:', pressResponse);
    }
  }, [finalResponse, pressResponse]);

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
            {pressResponse?.primary_statement || draftContent}
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

  // Active state - show the AI-generated crisis response
  if (pressResponse) {
    return (
      <div className="bg-gray-900 border border-purple-500 rounded-lg p-4 h-full overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Send className="w-4 h-4 text-purple-400 mr-2" />
            <h3 className="text-purple-400 font-mono text-sm font-bold tracking-wider">
              CRISIS RESPONSE
            </h3>
          </div>
          <div className="flex items-center space-x-2">
            {pressResponse.legal_compliance ? (
              <Shield className="w-4 h-4 text-green-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
            )}
            <span className="text-xs text-gray-400">
              {Math.round(pressResponse.confidence * 100)}% confident
            </span>
          </div>
        </div>
        
        {/* Primary Statement */}
        <div className="bg-purple-900/20 border border-purple-700 rounded p-3 mb-4">
          <div className="text-xs text-purple-300 mb-2 font-mono uppercase">
            Primary Statement ({pressResponse.tone})
          </div>
          <div className="text-gray-300 text-sm leading-relaxed">
            {pressResponse.primary_statement}
          </div>
        </div>

        {/* Key Messages */}
        {pressResponse.key_messages && pressResponse.key_messages.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-purple-300 mb-2 font-mono uppercase">
              Key Messages
            </div>
            <div className="bg-gray-800/50 border border-gray-700 rounded p-2">
              {pressResponse.key_messages.slice(0, 3).map((message, idx) => (
                <div key={idx} className="text-xs text-gray-400 mb-1">
                  • {message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Channel Responses */}
        {pressResponse.channels && (
          <div className="mb-4">
            <div className="text-xs text-purple-300 mb-2 font-mono uppercase">
              Channel Versions
            </div>
            <div className="space-y-2">
              <div className="bg-gray-800/50 border border-gray-700 rounded p-2">
                <div className="text-xs text-cyan-400 mb-1">📱 Social Media</div>
                <div className="text-xs text-gray-400">
                  {pressResponse.channels.social_media?.substring(0, 100)}...
                </div>
              </div>
              <div className="bg-gray-800/50 border border-gray-700 rounded p-2">
                <div className="text-xs text-yellow-400 mb-1">👥 Employee Memo</div>
                <div className="text-xs text-gray-400">
                  {pressResponse.channels.employee_memo?.substring(0, 100)}...
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Compliance & Risk */}
        <div className="flex items-center justify-between mb-4 text-xs">
          <div className="flex items-center space-x-1">
            {pressResponse.legal_compliance ? (
              <>
                <Shield className="w-3 h-3 text-green-400" />
                <span className="text-green-400">Legal Compliant</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-3 h-3 text-yellow-400" />
                <span className="text-yellow-400">Legal Review Needed</span>
              </>
            )}
          </div>
          {pressResponse.reputational_risk && (
            <span className="text-gray-400">
              Risk: {pressResponse.reputational_risk.toUpperCase()}
            </span>
          )}
        </div>
        
        {/* Fun Marketing Suggestion */}
        <div className="bg-gradient-to-r from-pink-900/20 to-purple-900/20 border border-pink-500/50 rounded-lg p-3 mb-4">
          <div className="flex items-center mb-2">
            <span className="text-lg mr-2">✨</span>
            <div className="text-xs text-pink-300 font-mono uppercase tracking-wider">
              Bonus Marketing Idea
            </div>
          </div>
          <div className="text-sm text-gray-300 leading-relaxed mb-2">
            💡 <strong className="text-pink-400">Celebrity Video Opportunity: </strong>
            Commission Gwyneth Paltrow for a "Thank you for your interest in Astronomer" video.
          </div>
          <div className="text-xs text-gray-400 italic">
            "Thank you for your interest in Astronomer... where data flies as naturally as our CEO." ✨
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
  }

  // Fallback to original display
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
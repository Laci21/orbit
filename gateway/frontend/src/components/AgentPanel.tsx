import React from 'react';
import { Agent } from '../data/mockData';

interface AgentPanelProps {
  agents: Agent[];
}

export const AgentPanel: React.FC<AgentPanelProps> = ({ agents }) => {
  return (
    <div className="bg-gray-900 border-2 border-cyan-400 rounded-lg p-6 h-full shadow-lg shadow-cyan-400/20">
      <div className="flex items-center mb-4">
        <div className="w-4 h-4 bg-cyan-400 rounded-full animate-pulse mr-3 shadow-lg shadow-cyan-400/50"></div>
        <h3 className="text-cyan-400 font-mono text-lg font-bold tracking-wider glow-text">
          AGENT STATUS
        </h3>
      </div>
      
      <div className="space-y-4">
        {agents.map((agent) => (
          <div 
            key={agent.id} 
            className={`border-2 rounded-lg p-4 transition-all duration-500 transform ${
              agent.status === 'active' 
                ? 'border-green-400 bg-green-900/30 shadow-xl shadow-green-400/30 scale-105 animate-pulse' 
                : agent.status === 'complete'
                ? 'border-blue-400 bg-blue-900/30 shadow-lg shadow-blue-400/20'
                : agent.status === 'error'
                ? 'border-red-400 bg-red-900/30 shadow-lg shadow-red-400/20'
                : 'border-gray-600 bg-gray-800/30'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <span className="text-3xl mr-3">{agent.avatar}</span>
                <div>
                  <div className="text-white font-mono text-sm font-bold">
                    {agent.name.toUpperCase()}
                  </div>
                  <div className="text-gray-400 text-sm">
                    {agent.description}
                  </div>
                </div>
              </div>
              <div className={`w-4 h-4 rounded-full ${
                agent.status === 'active' 
                  ? 'bg-green-400 animate-pulse shadow-lg shadow-green-400/50' 
                  : agent.status === 'complete'
                  ? 'bg-blue-400 shadow-lg shadow-blue-400/50'
                  : agent.status === 'error'
                  ? 'bg-red-400 shadow-lg shadow-red-400/50'
                  : 'bg-gray-600'
              }`}></div>
            </div>
            
            {agent.currentAction && agent.status === 'active' && (
              <div className="text-green-300 text-sm font-mono animate-pulse bg-green-900/20 p-2 rounded border border-green-700">
                <span className="text-green-400">▶</span> {agent.currentAction}
              </div>
            )}
            
            {agent.status === 'complete' && (
              <div className="text-green-300 text-sm font-mono bg-green-900/20 p-2 rounded border border-green-700">
                <span className="text-green-400">✓</span> Task completed
              </div>
            )}
            
            {agent.status === 'error' && (
              <div className="text-red-300 text-sm font-mono bg-red-900/20 p-2 rounded border border-red-700">
                <span className="text-red-400">✗</span> Error occurred
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Agent Collaboration Indicator */}
      <div className="mt-6 pt-4 border-t border-cyan-700">
        <div className="flex items-center justify-center space-x-2">
          <div className="flex items-center space-x-1">
            {agents.filter(a => a.status === 'active').length > 0 && (
              <>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping"></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping animation-delay-75"></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping animation-delay-150"></div>
              </>
            )}
          </div>
          <span className="text-cyan-400 font-mono text-xs font-bold">
            {agents.filter(a => a.status === 'active').length > 0 
              ? 'AGENTS COLLABORATING' 
              : agents.filter(a => a.status === 'error').length > 0
              ? 'SYSTEM ERROR DETECTED'
              : agents.filter(a => a.status === 'complete').length > 0
              ? 'MISSION COMPLETE'
              : 'AGENTS STANDBY'
            }
          </span>
        </div>
      </div>
    </div>
  );
};
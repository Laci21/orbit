import React from 'react';
import { Agent } from '../data/mockData';

interface AgentPanelProps {
  agents: Agent[];
}

export const AgentPanel: React.FC<AgentPanelProps> = ({ agents }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'complete': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '▶';
      case 'complete': return '✓';
      case 'error': return '✗';
      default: return '◯';
    }
  };

  return (
    <div className="bg-gray-900 border-2 border-cyan-400 rounded-xl p-6 h-full shadow-lg shadow-cyan-400/20">
      {/* Header */}
      <div className="flex items-center mb-6">
        <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse mr-3 shadow-lg shadow-cyan-400/50"></div>
        <h3 className="text-cyan-400 font-mono text-xl font-bold tracking-wider">
          AGENT STATUS
        </h3>
      </div>
      
      {/* Agent Grid - 2 columns */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {agents.map((agent) => {
          const color = getStatusColor(agent.status);
          return (
            <div 
              key={agent.id} 
              className={`relative border-2 rounded-xl p-4 transition-all duration-300 hover:scale-[1.02] ${
                agent.status === 'active' 
                  ? 'border-green-400 bg-gradient-to-br from-green-900/40 to-green-800/20 shadow-lg shadow-green-400/20' 
                  : agent.status === 'complete'
                  ? 'border-blue-400 bg-gradient-to-br from-blue-900/40 to-blue-800/20 shadow-lg shadow-blue-400/15'
                  : agent.status === 'error'
                  ? 'border-red-400 bg-gradient-to-br from-red-900/40 to-red-800/20 shadow-lg shadow-red-400/15'
                  : 'border-gray-600 bg-gradient-to-br from-gray-800/40 to-gray-700/20 hover:border-gray-500'
              }`}
            >
              {/* Status Indicator */}
              <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                agent.status === 'active' 
                  ? 'bg-green-400 text-green-900 animate-pulse shadow-lg shadow-green-400/50' 
                  : agent.status === 'complete'
                  ? 'bg-blue-400 text-blue-900 shadow-lg shadow-blue-400/50'
                  : agent.status === 'error'
                  ? 'bg-red-400 text-red-900 shadow-lg shadow-red-400/50'
                  : 'bg-gray-600 text-gray-300'
              }`}>
                {getStatusIcon(agent.status)}
              </div>

              {/* Agent Info */}
              <div className="text-center">
                <div className="text-4xl mb-2 filter drop-shadow-lg">
                  {agent.avatar}
                </div>
                <div className="text-white font-mono text-xs font-bold mb-1 tracking-wide">
                  {agent.name.toUpperCase()}
                </div>
                <div className="text-gray-400 text-xs leading-tight">
                  {agent.description}
                </div>
              </div>

              {/* Status Message */}
              {agent.currentAction && agent.status === 'active' && (
                <div className="mt-3 text-center">
                  <div className="text-green-300 text-xs font-mono animate-pulse bg-green-900/30 px-2 py-1 rounded border border-green-700">
                    {agent.currentAction}
                  </div>
                </div>
              )}
              
              {agent.status === 'complete' && (
                <div className="mt-3 text-center">
                  <div className="text-blue-300 text-xs font-mono bg-blue-900/30 px-2 py-1 rounded border border-blue-700">
                    COMPLETED
                  </div>
                </div>
              )}
              
              {agent.status === 'error' && (
                <div className="mt-3 text-center">
                  <div className="text-red-300 text-xs font-mono bg-red-900/30 px-2 py-1 rounded border border-red-700">
                    ERROR
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Mission Status Summary */}
      <div className="border-t border-cyan-700/50 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              {agents.filter(a => a.status === 'active').length > 0 && (
                <>
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping"></div>
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping animation-delay-75"></div>
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping animation-delay-150"></div>
                </>
              )}
            </div>
            <span className="text-cyan-400 font-mono text-sm font-bold tracking-wide">
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
          
          {/* Progress Indicator */}
          <div className="flex items-center space-x-2">
            <div className="text-xs text-gray-400 font-mono">
              {agents.filter(a => a.status === 'complete').length}/{agents.length}
            </div>
            <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
                style={{ width: `${(agents.filter(a => a.status === 'complete').length / agents.length) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};